import fitz  # PyMuPDF
import pandas as pd  # for CSV processing
import json
import re
from time import time
import os
from tqdm import tqdm
import datetime

# -------------------------------
# User Inputs
# -------------------------------
user_email = "trial.solutions@advancediscovery.io"
project_information = input("Enter project and database: ")

existing_annotation_csv_file = input("Paste CSV file path of existing annotations: ").strip().strip('"')
pdf_directory = input("Paste directory containing PDF files: ").strip().strip('"')

# Normalize paths
existing_annotation_csv_file = os.path.normpath(existing_annotation_csv_file)
pdf_dir = os.path.normpath(pdf_directory)

# Determine delimiter based on file extension
delimiter = '\t' if existing_annotation_csv_file.endswith('.txt') else ','

# Output paths
output_dir = os.path.dirname(existing_annotation_csv_file)
current_date = datetime.datetime.now().strftime("%Y%m%d")
annotation_output_csv = os.path.join(output_dir, f"{current_date}_{project_information}_combined_annotation_output.csv")
phrases_output_csv = os.path.join(output_dir, f"{current_date}_{project_information}_combined_phrases_output.csv")

# -------------------------------
# Regex Pattern and Stamp Constants
# -------------------------------
regex_pattern = (
    r'([A-Z]{3,5}\.\s*[A-Z0-9]{3,4}\.\s*[0-9]{3,4}\.\s*[0-9]{3,6}(_\d{4})?)|'
    r'(Exhibit\s+(PLE|CWS|CE|RE|CL|RL|TER|JER|CEX|REX|ORD|TRX|SBM)-[A-Z0-9]{3,4}(?:-[A-Z0-9]{2,4})?(_\d{4})?)|'
    r'((PLE|CWS|CE|RE|CL|RL|TER|JER|CEX|REX|ORD|TRX|SBM)-[A-Z0-9]{2,4}(?:-[A-Z0-9]{2,4})?(_\d{4})?)|'
    r'(REX-[A-Z0-9]{3,4}\.[A-Z0-9]{3,4}(_\d{4})?)|'
    r'(Exhibit\s+(REX-[A-Z0-9]{3,4}\.[A-Z0-9]{3,4}(_\d{4})?))|'
    r'((CC|RC|TC|JC)\.[A-Z0-9]{3,4}[A-Z]?\.[A-Z0-9]{3}(_\d{4})?)|'
    r'(Exhibit\s+(CC|RC|TC|JC)\.[A-Z0-9]{3,4}[A-Z]?\.[A-Z0-9]{3}(_\d{4})?)'
)
STAMP_WIDTH = 100  
STAMP_HEIGHT = 50  

# -------------------------------
# Output Containers
# -------------------------------
annotation_data_list = []  # Will be re-built after processing AttyNotes
phrase_matches_list = []   # Record for each matched phrase (used later for AttyNotes)

# Set to avoid duplicate annotations within this run (using tuple of markedText, cleaned note text, page, and rectangle coordinates)
added_annotations = set()

# -------------------------------
# Helper Function: Clean Note Text for Deduplication Key
# -------------------------------
def clean_note_for_key(note_text):
    """
    Removes surrounding <p> tags (if present) and then removes a trailing suffix 
    of the form _ followed by 4 digits.
    """
    note_text = note_text.strip()
    if note_text.startswith("<p>") and note_text.endswith("</p>"):
        note_text = note_text[3:-4].strip()
    note_text = re.sub(r'_\d{4}$', '', note_text)
    return note_text

# -------------------------------
# Function: Create Highlight Annotation Data
# -------------------------------
def create_annotation_data(rect, page_num, marked_text, link="Auto Annotated", user=user_email):
    timestamp = int(time() * 1000)
    marked_text = marked_text.strip()
    # For the note text we remove a trailing _#### suffix (if present) from the marked text.
    cleaned_note = re.sub(r'_\d{4}$', '', marked_text)
    note_text = f"<p>{cleaned_note}</p>"
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
                "text": note_text,
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
    # Deduplication key uses the marked text and the cleaned note text.
    annotation_key = (marked_text, cleaned_note, page_num, rect.x0, rect.y0, rect.width, rect.height)
    if annotation_key not in added_annotations:
        added_annotations.add(annotation_key)
        return annotation_data
    return None

# -------------------------------
# Helper Function: Get Deduplication Key for Annotations
# -------------------------------
def get_dedup_key(annotation):
    marked_text = annotation.get("markedText", "").strip()
    note_text = ""
    if annotation.get("notes") and len(annotation.get("notes")) > 0:
        note_text = annotation["notes"][0].get("text", "").strip()
    note_key = clean_note_for_key(note_text)
    page_num = annotation.get("rectangles", {}).get("pageNum", 0)
    rect_data = annotation.get("rectangles", {}).get("rectangles", [{}])[0]
    x = rect_data.get("x", 0)
    y = rect_data.get("y", 0)
    width = rect_data.get("width", 0)
    height = rect_data.get("height", 0)
    return (marked_text, note_key, page_num, x, y, width, height)

# -------------------------------
# Load Existing Annotation Data
# -------------------------------
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

# -------------------------------
# Recursively Find PDF Files in Subdirectories
# -------------------------------
pdf_files = []
for root, dirs, files in os.walk(pdf_dir):
    for file in files:
        if file.lower().endswith('.pdf'):
            pdf_files.append(os.path.join(root, file))

# -------------------------------
# Process Each PDF File (with Outer and Inner Progress Bars)
# -------------------------------
for full_pdf_path in tqdm(pdf_files, desc="Processing PDFs", unit="pdf"):
    pdf_file = os.path.basename(full_pdf_path)
    bates = os.path.splitext(pdf_file)[0]
    doc = fitz.open(full_pdf_path)
    new_annotations = []
    # Record phrase matches with document, found text, and page (pages are 0-indexed)
    pdf_phrase_matches = []
    
    # Inner progress bar for pages in the current PDF.
    for page_num in tqdm(range(len(doc)), desc=f"Scanning {pdf_file}", unit="page", leave=False):
        page = doc.load_page(page_num)
        page_rect = page.rect
        stamp_area = fitz.Rect(page_rect.x1 - STAMP_WIDTH, page_rect.y0, page_rect.x1, page_rect.y0 + STAMP_HEIGHT)
        page_text = page.get_text("text")
        
        for match in re.finditer(regex_pattern, page_text, re.IGNORECASE):
            found_text = match.group(0).strip()
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
                        'Page': page_num  # 0-indexed; will be converted later
                    })
    doc.close()
    
    # Merge new highlights with existing highlights for this Bates.
    orig_obj = original_annotations.get(bates, {})
    if "Highlights" in orig_obj and orig_obj["Highlights"]:
        try:
            existing_highlights = [json.loads(x) for x in orig_obj["Highlights"].split("\u0013") if x]
        except Exception:
            existing_highlights = []
    else:
        existing_highlights = []
    
    if new_annotations:
        unique_new = []
        seen = set()
        for annot in new_annotations:
            key = get_dedup_key(annot)
            if key not in seen:
                seen.add(key)
                unique_new.append(annot)
        existing_keys = {get_dedup_key(a) for a in existing_highlights}
        new_to_add = [annot for annot in unique_new if get_dedup_key(annot) not in existing_keys]
        combined_highlights = existing_highlights + new_to_add
        combined_annotations_str = "\u0013".join([json.dumps(annot) for annot in combined_highlights])
        orig_obj["Highlights"] = combined_annotations_str
    original_annotations[bates] = orig_obj
    phrase_matches_list.extend(pdf_phrase_matches)

# -------------------------------
# Update AttyNotes Data Based on Regex Matches
# -------------------------------
# Add a progress bar for updating AttyNotes for each document.
for bates in tqdm(list(original_annotations.keys()), desc="Updating AttyNotes", unit="document"):
    refers_to_set = set()
    referenced_in_set = set()
    for rec in phrase_matches_list:
        page_str = f"{rec['Page']+1:04d}"
        # For the same document, remove the trailing _#### for display in "Refers To"
        if rec['Bates/Control #'] == bates:
            cleaned_text = re.sub(r'_\d{4}$', '', rec['Found Text'])
            refers_to_set.add(f"{cleaned_text} at {page_str}")
        else:
            # For a different document, use the full found text (with suffix intact)
            # to match if it equals the current Bates or starts with the Bates plus an underscore.
            if rec['Found Text'] == bates or rec['Found Text'].startswith(bates + "_"):
                referenced_in_set.add(f"{rec['Bates/Control #']} at {page_str}")
    # Build the AttyNotes text with bold headers.
    new_atty_text = (
        "<p><strong>Refers To:</strong></p>\n<p>&nbsp;</p>\n" +
        "\n".join(f"<p>{entry}</p>" for entry in sorted(refers_to_set)) +
        "\n<p>&nbsp;</p>\n<p><strong>Referenced In:</strong></p>\n<p>&nbsp;</p>\n" +
        "\n".join(f"<p>{entry}</p>" for entry in sorted(referenced_in_set)) +
        "\n<p>&nbsp;</p>\n<p><strong>Transcript:</strong></p>"
    )
    timestamp = int(time() * 1000)
    orig_obj = original_annotations[bates]
    # Parse existing AttyNotes if present.
    existing_atty = []
    if "AttyNotes" in orig_obj and orig_obj["AttyNotes"]:
        parts = orig_obj["AttyNotes"].split("\u0013")
        for part in parts:
            part = part.strip()
            if part:
                try:
                    note_obj = json.loads(part)
                    existing_atty.append(note_obj)
                except Exception:
                    pass

    # Separate existing AttyNotes into non-trial and trial.
    existing_non_trial = [a for a in existing_atty if a.get("user", "").lower() != "trial.solutions@advancediscovery.io"]
    trial_existing = [a for a in existing_atty if a.get("user", "").lower() == "trial.solutions@advancediscovery.io"]
    
    if trial_existing:
        existing_trial = trial_existing[0]
        if new_atty_text not in existing_trial.get("text", ""):
            existing_trial["text"] = new_atty_text
            existing_trial["updated"] = timestamp
        new_trial_record = existing_trial
    else:
        new_trial_record = {
            "text": new_atty_text,
            "created": timestamp,
            "updated": timestamp,
            "parentType": "Document",
            "parentId": 0,
            "id": 0,
            "user": "trial.solutions@advancediscovery.io",
            "unit": "point"
        }
    
    combined_atty_list = existing_non_trial + [new_trial_record]
    combined_atty_str = "\u0013".join(json.dumps(note) for note in combined_atty_list)
    orig_obj["AttyNotes"] = combined_atty_str
    original_annotations[bates] = orig_obj

# -------------------------------
# Rebuild the Output List to Include Updated AttyNotes (with progress bar)
# -------------------------------
annotation_data_list = [
    {'Bates/Control #': bates, 'Annotation Data': json.dumps(obj) if obj else ""}
    for bates, obj in tqdm(original_annotations.items(), desc="Rebuilding Output List", unit="document")
]

# -------------------------------
# Write Outputs to CSV Files
# -------------------------------
annotation_df = pd.DataFrame(annotation_data_list)
phrase_matches_df = pd.DataFrame(phrase_matches_list)

annotation_df.to_csv(annotation_output_csv, index=False, encoding='utf-8')
phrase_matches_df.to_csv(phrases_output_csv, index=False, encoding='utf-8')
print(f"Annotation CSV written to {annotation_output_csv}")
print(f"Phrases CSV written to {phrases_output_csv}")
