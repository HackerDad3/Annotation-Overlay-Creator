import fitz  # PyMuPDF
import pandas as pd  # for CSV processing
import json
import re
from time import time
import os
from tqdm import tqdm
import datetime

# User email to show in notes
user_email = "trial.solutions@advancediscovery.io"

# My regex patterns
regex_pattern = (
    r'([A-Z]{3,5}\.\s*[A-Z0-9]{3,4}\.\s*[0-9]{3,4}\.\s*[0-9]{3,6}(_\d{4})?)|'
    r'(Exhibit\s+(PLE|CWS|CE|RE|CL|RL|TER|JER|CEX|REX|ORD|TRX)-[A-Z0-9]{3,4}(?:-[A-Z0-9]{2,4})?(_\d{4})?)|'
    r'((PLE|CWS|CE|RE|CL|RL|TER|JER|CEX|REX|ORD|TRX)-[A-Z0-9]{2,4}(?:-[A-Z0-9]{2,4})?(_\d{4})?)|'
    r'(REX-[A-Z0-9]{3,4}\.[A-Z0-9]{3,4}(_\d{4})?)|'
    r'(Exhibit\s+(REX-[A-Z0-9]{3,4}\.[A-Z0-9]{3,4}(_\d{4})?))|'
    r'((CC|RC|TC|JC)\.[A-Z0-9]{3,4}[A-Z]?\.[A-Z0-9]{3}(_\d{4})?)|'
    r'(Exhibit\s+(CC|RC|TC|JC)\.[A-Z0-9]{3,4}[A-Z]?\.[A-Z0-9]{3}(_\d{4})?)'
)

document_number = input("Main Document number: ")

# File paths: CSV of existing annotation data and directory of PDFs
existing_annotation_csv_file = input("Paste CSV file path of existing annotations: ").strip().strip('"')
pdf_directory = input("Paste directory containing PDF files: ").strip().strip('"')

# Normalize paths
existing_annotation_csv_file = os.path.normpath(existing_annotation_csv_file)
pdf_dir = os.path.normpath(pdf_directory)

# Determine delimiter based on file extension
delimiter = '\t' if existing_annotation_csv_file.endswith('.txt') else ','

# Output directory (same as input CSV file's directory)
output_dir = os.path.dirname(existing_annotation_csv_file)
current_date = datetime.datetime.now().strftime("%Y%m%d")

# Combined output file paths
annotation_output_csv = os.path.join(output_dir, f"{current_date}_{document_number}_combined_annotation_output.csv")
phrases_output_csv = os.path.join(output_dir, f"{current_date}_{document_number}_combined_phrases_output.csv")

# Constants for the stamp area (assumes each page has a Bates stamp at the top-right)
STAMP_WIDTH = 100  
STAMP_HEIGHT = 50  

# Initialize output containers
annotation_data_list = []
phrase_matches_list = []

# Set to avoid duplicate annotations (keyed by page, text, and coordinates)
added_annotations = set()

def create_annotation_data(rect, page_num, marked_text, link="Auto Annotated", user=user_email):
    """Creates an annotation dictionary (if not already added) for a found hit.
       Note: The notes text is set to the matched text (same as markedText)."""
    timestamp = int(time() * 1000)
    annotation_data = {
        "rectangles": {
            "rectangles": [
                {"x": rect.x0, "y": rect.y0, "width": rect.width, "height": rect.height}
            ],
            "pageNum": page_num,
            "color": "BLUE",
        },
        "created": timestamp,
        "updated": timestamp,
        "notes": [
            {
                "text": f"<p>{marked_text}</p>",
                "created": timestamp,
                "parentType": "Highlight",
                "parentId": 0,
                "id": 0,
                "user": user,
                "docId": 0,
                "security": ["WRITE", "READ", "ADMIN"],
            }
        ],
        "id": 0,
        "user": user,
        "unit": "point",
        "markedText": marked_text,
    }
    
    # Create a unique key based on page number, marked text, and bounding box
    annotation_key = (page_num, marked_text, rect.x0, rect.y0, rect.width, rect.height)
    if annotation_key not in added_annotations:
        added_annotations.add(annotation_key)
        return annotation_data
    return None

# === Load existing annotation data ===
# The CSV is expected to have columns: "Bates/Control #" and "Annotation Data"
existing_df = pd.read_csv(existing_annotation_csv_file, delimiter=delimiter)
original_annotations = {}
for index, row in existing_df.iterrows():
    bates = str(row['Bates/Control #']).strip()
    json_str = row['Annotation Data']
    try:
        obj = json.loads(json_str)
    except Exception:
        obj = {}
    original_annotations[bates] = obj

# === Process each PDF file ===
# Using an outer progress bar for files.
for pdf_file in tqdm(os.listdir(pdf_dir), desc="Processing PDFs", unit="pdf"):
    if pdf_file.lower().endswith('.pdf'):
        full_pdf_path = os.path.join(pdf_dir, pdf_file)
        bates = os.path.splitext(pdf_file)[0]
        doc = fitz.open(full_pdf_path)
        new_annotations = []
        pdf_phrase_matches = []
        
        # Inner progress bar for pages.
        for page_num in tqdm(range(len(doc)), desc=f"Processing pages in {pdf_file}", unit="page", leave=False):
            page = doc.load_page(page_num)
            page_rect = page.rect
            stamp_area = fitz.Rect(page_rect.x1 - STAMP_WIDTH, page_rect.y0, page_rect.x1, page_rect.y0 + STAMP_HEIGHT)
            page_text = page.get_text("text")
            
            for match in re.finditer(regex_pattern, page_text, re.IGNORECASE):
                found_text = match.group(0)
                for rect in page.search_for(found_text):
                    rect = fitz.Rect(rect)
                    intersection = rect & stamp_area
                    if rect.get_area() > 0 and (intersection.get_area() / rect.get_area() > 0.5):
                        continue
                    annot = create_annotation_data(rect, page_num, found_text)
                    if annot:
                        new_annotations.append(annot)
                        pdf_phrase_matches.append({
                            'Bates/Control #': bates,
                            'Found Text': found_text,
                            'Page': page_num
                        })
        doc.close()
        
        # Merge new highlights with existing highlights only if new highlights are found.
        orig_obj = original_annotations.get(bates, {})
        if "Highlights" in orig_obj and orig_obj["Highlights"]:
            try:
                existing_highlights = [json.loads(x.replace('\\"','"')) for x in orig_obj["Highlights"].split("\u0013") if x]
            except Exception:
                existing_highlights = []
        else:
            existing_highlights = []
        
        if new_annotations:
            # Deduplicate new highlights among themselves.
            unique_new = []
            seen = set()
            for annot in new_annotations:
                s = json.dumps(annot, sort_keys=True)
                if s not in seen:
                    seen.add(s)
                    unique_new.append(annot)
            # Deduplicate: always keep the original highlights; add only new highlights not present in the original.
            orig_set = {json.dumps(a, sort_keys=True) for a in existing_highlights}
            new_to_add = [annot for annot in unique_new if json.dumps(annot, sort_keys=True) not in orig_set]
            combined_highlights = existing_highlights + new_to_add
            combined_annotations_str = "\\u0013".join([json.dumps(annot).replace('"', '\\"') for annot in combined_highlights])
            orig_obj["Highlights"] = combined_annotations_str
        # If no new highlights, leave orig_obj unchanged.
        
        original_annotations[bates] = orig_obj
        annotation_data_list.append({
            'Bates/Control #': bates,
            'Annotation Data': json.dumps(orig_obj) if orig_obj else ""
        })
        phrase_matches_list.extend(pdf_phrase_matches)

# === Write outputs to CSV files ===
annotation_df = pd.DataFrame(annotation_data_list)
phrase_matches_df = pd.DataFrame(phrase_matches_list)

annotation_df.to_csv(annotation_output_csv, index=False, encoding='utf-8')
phrase_matches_df.to_csv(phrases_output_csv, index=False, encoding='utf-8')
print(f"Annotation CSV written to {annotation_output_csv}")
print(f"Phrases CSV written to {phrases_output_csv}")
