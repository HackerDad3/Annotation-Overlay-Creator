import fitz  # PyMuPDF
import pandas as pd
import re
import os
import json
from time import time
from tqdm import tqdm
import datetime

# User email for annotation notes
user_email = "trial.solutions@advancediscovery.io"

# --- Configuration ---
regex_pattern = (
    r'([A-Z]{3,5}\.\s*[A-Z0-9]{3,4}\.\s*[0-9]{3,4}\.\s*[0-9]{3,6}(_\d{4})?)|'
    r'(Exhibit\s+(PLE|CWS|CE|RE|CL|RL|TER|JER|CEX|REX|ORD|TRX)-[A-Z0-9]{3,4}(?:-[A-Z0-9]{2,4})?(_\d{4})?)|'
    r'((PLE|CWS|CE|RE|CL|RL|TER|JER|CEX|REX|ORD|TRX)-[A-Z0-9]{2,4}(?:-[A-Z0-9]{2,4})?(_\d{4})?)|'
    r'(REX-[A-Z0-9]{3,4}\.[A-Z0-9]{3,4}(_\d{4})?)|'
    r'(Exhibit\s+(REX-[A-Z0-9]{3,4}\.[A-Z0-9]{3,4}(_\d{4})?))|'
    r'((CC|RC|TC|JC)\.[A-Z0-9]{3,4}[A-Z]?\.[A-Z0-9]{3}(_\d{4})?)|'
    r'(Exhibit\s+(CC|RC|TC|JC)\.[A-Z0-9]{3,4}[A-Z]?\.[A-Z0-9]{3}(_\d{4})?)'
)

STAMP_WIDTH = 100  
STAMP_HEIGHT = 50

# --- User Inputs ---
pdf_directory = input("Enter directory containing PDF files: ").strip().strip('"')
pdf_directory = os.path.normpath(pdf_directory)

parent_dir = os.path.dirname(pdf_directory)
date_prefix = datetime.datetime.now().strftime("%Y%m%d")
output_csv_file = os.path.join(parent_dir, f"{date_prefix}_combined_annotation_output.csv")
report_csv_file = os.path.join(parent_dir, f"{date_prefix}_Regex_Report.csv")

# --- Load existing annotation data (if any) ---
existing_annotation_csv_file = input("Paste CSV file path of existing annotations: ").strip().strip('"')
existing_annotation_csv_file = os.path.normpath(existing_annotation_csv_file)
delimiter = '\t' if existing_annotation_csv_file.endswith('.txt') else ','
existing_df = pd.read_csv(existing_annotation_csv_file, delimiter=delimiter)
existing_annotations = {}
for index, row in existing_df.iterrows():
    bates = str(row['Bates/Control #'])
    annotation_json_str = row['Annotation Data']
    try:
        annotation_obj = json.loads(annotation_json_str)
        highlights = annotation_obj.get("Highlights", [])
        if not isinstance(highlights, list):
            highlights = []
        atty_str = annotation_obj.get("AttyNotes", "")
        if atty_str:
            try:
                atty_obj = json.loads(atty_str)
            except Exception:
                atty_obj = {}
        else:
            atty_obj = {}
    except Exception:
        highlights = []
        atty_obj = {}
    existing_annotations[bates] = {"Highlights": highlights, "AttyNotes": atty_obj}

# --- Gather all PDF files recursively ---
pdf_files = []
for root, dirs, files in os.walk(pdf_directory):
    for file in files:
        if file.lower().endswith('.pdf'):
            pdf_files.append(os.path.join(root, file))

# --- Initialize output containers ---
annotation_data_list = []  # Final combined annotation JSON per Bates
phrase_matches_list = []   # Report: individual regex occurrences
results = []               # For aggregating occurrences per Bates for AttyNotes

# --- Process each PDF file (record occurrences for AttyNotes only) ---
for pdf_path in tqdm(pdf_files, desc="Processing PDFs", unit="pdf"):
    pdf_file = os.path.basename(pdf_path)
    bates = os.path.splitext(pdf_file)[0]  # Bates/Control: filename without extension
    doc = fitz.open(pdf_path)
    pdf_matches = []
    for page_num in tqdm(range(len(doc)), desc=f"Processing pages in {pdf_file}", unit="page", leave=False):
        page = doc.load_page(page_num)
        page_rect = page.rect
        stamp_area = fitz.Rect(page_rect.x1 - STAMP_WIDTH, page_rect.y0, page_rect.x1, page_rect.y0 + STAMP_HEIGHT)
        page_text = page.get_text("text")
        
        # Find regex matches and remove line breaks from matched text.
        for match in re.finditer(regex_pattern, page_text, re.IGNORECASE):
            # Remove line breaks and extra whitespace
            found_text = re.sub(r'[\r\n]+', ' ', match.group(0)).strip()
            for rect in page.search_for(found_text):
                rect = fitz.Rect(rect)
                intersection = rect & stamp_area
                if rect.get_area() > 0 and (intersection.get_area() / rect.get_area() > 0.5):
                    continue
                pdf_matches.append({
                    'Bates/Control #': bates,
                    'Found Text': found_text,
                    'Page': page_num + 1
                })
                results.append({
                    "Bates": bates,
                    "Matched Text": found_text,
                    "Page": page_num + 1
                })
    doc.close()
    if pdf_matches:
        annotation_data_list.append({
            'Bates/Control #': bates,
            'Annotation Data': ""  # to be populated below
        })
        phrase_matches_list.extend(pdf_matches)

# --- Merge new occurrences into AttyNotes per Bates ---
agg = {}
for row in results:
    bates = row["Bates"]
    occ = f"{row['Matched Text']} at {str(row['Page']).zfill(4)}"
    if bates not in agg:
        agg[bates] = []
    if occ not in agg[bates]:
        agg[bates].append(occ)

# Define header and footer for the AttyNotes text (using plain HTML tags)
header = "<b>Refers to:</b> <br> "
footer = " <br><b>Referenced In:</b> <br><b><b>Transcript:</b></b> <br>"
for row in annotation_data_list:
    bates = row["Bates/Control #"]
    new_occurrences = agg.get(bates, [])
    
    # Get existing AttyNotes from the input JSON (if any)
    old_atty = existing_annotations.get(bates, {}).get("AttyNotes", {})
    if isinstance(old_atty, str):
        try:
            old_atty = json.loads(old_atty)
        except Exception:
            old_atty = {}
    old_occurrences = []
    if "text" in old_atty:
        txt = old_atty["text"]
        if txt.startswith(header) and txt.endswith(footer):
            mid = txt[len(header):-len(footer)]
            old_occurrences = [x.strip() for x in mid.split("<br>") if x.strip()]
        elif txt:
            old_occurrences = [txt]
    merged_occurrences = list(dict.fromkeys(old_occurrences + new_occurrences))
    if merged_occurrences:
        atty_text = header + " <br> ".join(merged_occurrences) + footer
    else:
        atty_text = ""
    merged_atty = {
        "text": atty_text,
        "created": old_atty.get("created", int(time() * 1000)),
        "updated": None,
        "parentType": "Document",
        "parentId": 0,
        "id": 0,
        "user": user_email,
        "unit": "point"
    }
    if bates in existing_annotations:
        final_obj = existing_annotations[bates].copy()
    else:
        final_obj = {}
    final_obj["AttyNotes"] = json.dumps(merged_atty)
    row["Annotation Data"] = json.dumps(final_obj)

# --- Write the combined annotation CSV (final JSON per Bates) ---
df_annotation = pd.DataFrame(annotation_data_list)
df_annotation.to_csv(output_csv_file, index=False, encoding='utf-8')
print(f"Combined Annotation CSV written to: {output_csv_file}")

# --- Write the second CSV report for regex matches ---
df_report = pd.DataFrame(phrase_matches_list)
df_report.to_csv(report_csv_file, index=False, encoding='utf-8')
print(f"Regex Report CSV written to: {report_csv_file}")
