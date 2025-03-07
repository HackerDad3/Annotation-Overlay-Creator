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
STAMP_WIDTH = 100  # adjust width (points) as needed
STAMP_HEIGHT = 50  # adjust height (points) as needed

# Initialize output containers
annotation_data_list = []
phrase_matches_list = []

# Set to avoid duplicate annotations (keyed by page, text, and coordinates)
added_annotations = set()

def create_annotation_data(rect, page_num, marked_text, link="Auto Annotated", user=user_email):
    """Creates an annotation dictionary (if not already added) for a found hit.
       Note: The notes text is now set to the matched text (same as markedText)."""
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
                "text": f"<p>{marked_text}</p>",  # updated: using matched text instead of link
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
existing_annotations = {}
for index, row in existing_df.iterrows():
    bates = str(row['Bates/Control #'])
    annotation_json_str = row['Annotation Data']
    try:
        annotation_obj = json.loads(annotation_json_str)
        highlights_str = annotation_obj.get("Highlights", "")
        if highlights_str:
            # The annotations were stored as JSON strings joined by \u0013; convert each back to dict
            annotations = [json.loads(x.replace('\\"', '"')) for x in highlights_str.split("\u0013") if x]
        else:
            annotations = []
    except Exception as e:
        annotations = []
    existing_annotations[bates] = annotations

# === Define the regex pattern ===
regex_pattern = r'([A-Z]{3,5}\.\s*[A-Z0-9]{3,4}\.\s*[0-9]{3,4}\.\s*[0-9]{3,6}(_\d{4})?)|(Exhibit\s+(PLE|CWS|CE|RE|CL|RL|TER|JER|CEX|REX|ORD|TRX)-\d{3,4}(_\d{4})?)|((PLE|CWS|CE|RE|CL|RL|TER|JER|CEX|REX|ORD|TRX)-\d{2,4}(_\d{4})?)|(REX-\d{3,4}\.\d{3,4}(_\d{4})?)|(Exhibit\s+(REX-\d{3,4}\.\d{3,4}(_\d{4})?))|((CC|RC|TC|JC)\.\d{3,4}[A-Z]?\.\d{3}(_\d{4})?)|(Exhibit\s+(CC|RC|TC|JC)\.\d{3,4}[A-Z]?\.\d{3}(_\d{4})?)'

# === Gather all PDF files from directory and subdirectories ===
pdf_files = []
for root, dirs, files in os.walk(pdf_dir):
    for file in files:
        if file.lower().endswith('.pdf'):
            pdf_files.append(os.path.join(root, file))

# === Process each PDF file using a progress bar for total PDFs ===
for pdf_path in tqdm(pdf_files, desc="Processing PDFs", unit="pdf"):
    pdf_file = os.path.basename(pdf_path)
    # The Bates number is assumed to be the file name without extension
    bates = os.path.splitext(pdf_file)[0]
    doc = fitz.open(pdf_path)
    new_annotations = []
    pdf_phrase_matches = []
    
    # Progress bar for pages in the current PDF file
    for page_num in tqdm(range(len(doc)), desc=f"Processing pages in {pdf_file}", unit="page", leave=False):
        page = doc.load_page(page_num)
        page_rect = page.rect
        # Define the stamp area (top-right corner)
        stamp_area = fitz.Rect(page_rect.x1 - STAMP_WIDTH, page_rect.y0, page_rect.x1, page_rect.y0 + STAMP_HEIGHT)
        page_text = page.get_text("text")
        
        # Search for regex hits on the page
        for match in re.finditer(regex_pattern, page_text, re.IGNORECASE):
            found_text = match.group(0)
            # Use search_for to get all bounding boxes for the found text
            for rect in page.search_for(found_text):
                rect = fitz.Rect(rect)
                # Check overlap with stamp area (skip if >50% of the hit lies in the stamp region)
                intersection = rect & stamp_area
                if rect.get_area() > 0 and (intersection.get_area() / rect.get_area() > 0.5):
                    continue
                annotation = create_annotation_data(rect, page_num, found_text)
                if annotation:
                    new_annotations.append(annotation)
                    pdf_phrase_matches.append({
                        'Bates/Control #': bates,
                        'Found Text': found_text,
                        'Page': page_num
                    })
    doc.close()
    
    # Merge any new annotations with existing ones for this Bates number
    existing_annots = existing_annotations.get(bates, [])
    combined_annots = existing_annots + new_annotations
    
    if combined_annots:
        # Join each annotation (JSON-dumped and with escaped quotes) using \u0013 as the separator
        combined_annotations_str = "\u0013".join([json.dumps(annot).replace('"', '\\"') for annot in combined_annots])
        annotation_json = f'{{"Highlights":"{combined_annotations_str}"}}'
    else:
        annotation_json = '{"Highlights":""}'
    
    annotation_data_list.append({
        'Bates/Control #': bates,
        'Annotation Data': annotation_json
    })
    phrase_matches_list.extend(pdf_phrase_matches)

# === Write the combined outputs to CSV files ===
annotation_df = pd.DataFrame(annotation_data_list)
phrase_matches_df = pd.DataFrame(phrase_matches_list)

annotation_df.to_csv(annotation_output_csv, index=False, encoding='utf-8')
phrase_matches_df.to_csv(phrases_output_csv, index=False, encoding='utf-8')
