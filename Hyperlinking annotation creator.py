import fitz  # PyMuPDF
import csv
import json
import re
from time import time
import os
from tqdm import tqdm

# User email to show in notes
user_email = "trial.solutions@advancediscovery.io"

# File paths
input_csv_file = input("Paste CSV file path: ").strip().strip('"')
pdf_directory = input("Paste directory containing PDF files: ").strip().strip('"')

# Normalize paths
input_file = os.path.normpath(input_csv_file)
pdf_dir = os.path.normpath(pdf_directory)

# Determine delimiter based on file extension
input_delimiter = '\t' if input_file.endswith('.txt') else ','

# Output directory (same as input CSV file's directory)
output_dir = os.path.dirname(input_file)

# Combined output file paths
annotation_output_csv = os.path.join(output_dir, "combined_annotation_output.csv")
phrases_output_csv = os.path.join(output_dir, "combined_phrases_output.csv")

# Initialize the output files with headers
if not os.path.exists(annotation_output_csv):
    with open(annotation_output_csv, mode='w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Bates/Control #', 'Annotation Data']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

if not os.path.exists(phrases_output_csv):
    with open(phrases_output_csv, mode='w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Document', 'Phrase', 'Matched']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

# Function to normalize text
def normalize_text(text):
    """Normalize text for consistent matching."""
    return (
        text.replace('–', '-')  # Replace en dash with hyphen
            .replace('—', '-')  # Replace em dash with hyphen
            .replace('“', '"')  # Replace left double quotes
            .replace('”', '"')  # Replace right double quotes
            .replace('‘', "'")  # Replace left single quotes
            .replace('’', "'")  # Replace right single quotes
            .lower()  # Make the text lowercase for case-insensitive comparison
    )

# Function to generate the escaped JSON string for annotation data
def create_annotation_data(rectangles, page_num, phrase, link, user=user_email):
    timestamp = int(time() * 1000)  # Current time in milliseconds
    annotation_data = {
        "rectangles": {
            "rectangles": [
                {
                    "x": rectangles.x0,
                    "y": rectangles.y0,
                    "width": rectangles.width,
                    "height": rectangles.height
                }
            ],
            "pageNum": page_num,
            "color": "BLUE"
        },
        "created": timestamp,
        "updated": timestamp,
        "notes": [
            {
                "text": f"<p>{link}</p>",
                "created": timestamp,
                "parentType": "Highlight",
                "parentId": 0,
                "id": 0,
                "user": user,
                "docId": 0,
                "security": ["WRITE", "READ", "ADMIN"]
            }
        ],
        "id": 0,
        "user": user,
        "unit": "point",
        "markedText": phrase
    }
    return json.dumps(annotation_data).replace('"', '\\"')

# Read the target phrases and their links from the input file
with open(input_file, newline='', encoding='utf-8') as file:
    reader = list(csv.DictReader(file, delimiter=input_delimiter))  # Convert to list for tqdm progress bar

# Process each PDF in the directory
for pdf_file in tqdm(os.listdir(pdf_dir), desc="Processing PDFs"):
    if pdf_file.endswith('.pdf'):
        pdf_path = os.path.join(pdf_dir, pdf_file)
        pdf_filename_no_ext = os.path.splitext(os.path.basename(pdf_path))[0]

        # Open the PDF file
        doc = fitz.open(pdf_path)

        # Create a set to track unique annotations
        unique_annotations = set()  # Store tuples of (page_num, x0, y0, width, height, marked_text, notes_text)
        phrase_matches = []  # To track matches for this document

        for row in tqdm(reader, desc=f"Processing phrases in {pdf_file}"):
            phrase = normalize_text(row['Reference'])  # Normalize phrase from CSV
            link = row['Link']
            matched = False  # Flag to track if the phrase is matched

            # 1. **Search for Exact Matches Using Regex**
            word_boundary_pattern = rf"\b{re.escape(phrase)}\b(?![_\w])"  # Exact match, no trailing alphanumeric or underscores
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                page_text = normalize_text(page.get_text("text"))  # Normalize PDF text
                for match in re.finditer(word_boundary_pattern, page_text, re.IGNORECASE):
                    matched = True

                    # Extract the matched text's location
                    quads = page.search_for(match.group())
                    for quad in quads:
                        rect = fitz.Rect(quad)
                        annotation_key = (page_num, rect.x0, rect.y0, rect.width, rect.height, match.group(), link)
                        if annotation_key not in unique_annotations:
                            unique_annotations.add(annotation_key)  # Add the annotation key to the set

            # 2. **Search for Multi-Line Matches**
            if not matched:  # Only if no exact match was found
                flexible_pattern = re.escape(phrase)
                flexible_pattern = flexible_pattern.replace(r'\-', r'\-\s*').replace(r'\ ', r'\s+')
                flexible_pattern = rf"\b{flexible_pattern}\b(?![_\w])"

                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    page_text = normalize_text(page.get_text("text"))  # Normalize PDF text

                    for match in re.finditer(flexible_pattern, page_text, re.IGNORECASE):
                        matched = True

                        # Highlight each line within the match to handle line breaks
                        start, end = match.span()
                        match_text = page_text[start:end]
                        lines = match_text.splitlines()

                        for line in lines:
                            quads = page.search_for(line)
                            for quad in quads:
                                rect = fitz.Rect(quad)
                                annotation_key = (page_num, rect.x0, rect.y0, rect.width, rect.height, line, link)
                                if annotation_key not in unique_annotations:
                                    unique_annotations.add(annotation_key)  # Add the annotation key to the set

            # Log the match status for this phrase
            phrase_matches.append({'Document': pdf_filename_no_ext, 'Phrase': row['Reference'], 'Matched': 'Yes' if matched else 'No'})

        # Append annotations to the single output CSV
        if unique_annotations:
            all_annotations = []
            for annotation in unique_annotations:
                page_num, x0, y0, width, height, marked_text, notes_text = annotation
                rect = fitz.Rect(x0, y0, x0 + width, y0 + height)
                annotation_data = create_annotation_data(rect, page_num, marked_text, notes_text)
                all_annotations.append(annotation_data)

            combined_annotations = "\\u0013".join(all_annotations)
            annotation_json = f"{{\"Highlights\":\"{combined_annotations}\"}}"
            with open(annotation_output_csv, mode='a', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=['Bates/Control #', 'Annotation Data'])
                writer.writerow({'Bates/Control #': pdf_filename_no_ext, 'Annotation Data': annotation_json})

        # Append phrase matches to the single output CSV
        with open(phrases_output_csv, mode='a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=['Document', 'Phrase', 'Matched'])
            writer.writerows(phrase_matches)

        # Close the PDF document
        doc.close()
