import fitz  # PyMuPDF
import pandas as pd  # Import pandas for CSV processing
import json
import re
from time import time
import os
from tqdm import tqdm
import datetime

# User email to show in notes
user_email = "trial.solutions@advancediscovery.io"

document_number = input("Main Document number: ")

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

current_date = datetime.datetime.now().strftime("%Y%m%d")

# Combined output file paths
annotation_output_csv = os.path.join(output_dir, f"{current_date}_{document_number}_combined_annotation_output.csv")
phrases_output_csv = os.path.join(output_dir, f"{current_date}_{document_number}_combined_phrases_output.csv")

# Initialize the output data
annotation_data_list = []
phrase_matches_list = []

# Initialize a set to track unique annotations based on page number, marked text, and coordinates
added_annotations = set()

# Function to generate the escaped JSON string for annotation data
def create_annotation_data(rectangles, page_num, phrase, link, user=user_email):
    timestamp = int(time() * 1000)
    annotation_data = {
        "rectangles": {
            "rectangles": [
                {"x": rectangles.x0, "y": rectangles.y0, "width": rectangles.width, "height": rectangles.height}
            ],
            "pageNum": page_num,
            "color": "BLUE",
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
                "security": ["WRITE", "READ", "ADMIN"],
            }
        ],
        "id": 0,
        "user": user,
        "unit": "point",
        "markedText": phrase,
    }

    # Create a unique identifier for the annotation (combination of page number, bounding box, and marked text)
    annotation_key = (page_num, phrase, rectangles.x0, rectangles.y0, rectangles.width, rectangles.height)
    
    # If the annotation has not been added before, add it to the set and return the annotation data
    if annotation_key not in added_annotations:
        added_annotations.add(annotation_key)
        return annotation_data
    
    # If the annotation is a duplicate, return None
    return None

# Read CSV using pandas (this will handle large CSV fields)
df = pd.read_csv(input_file, delimiter=input_delimiter)

# Process each PDF in the directory
for pdf_file in tqdm(os.listdir(pdf_dir), desc="Processing PDFs"):
    if pdf_file.endswith('.pdf'):
        pdf_path = os.path.join(pdf_dir, pdf_file)

        doc = fitz.open(pdf_path)
        all_annotations = []
        phrase_matches = []

        for _, row in tqdm(df.iterrows(), desc=f"Processing phrases in {pdf_file}", total=df.shape[0]):
            phrase = row['Reference']
            link = row['Link']
            matched = False

            # Search for exact matches
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                instances = page.search_for(phrase)

                if instances:
                    matched = True
                    for inst in instances:
                        rect = fitz.Rect(inst)
                        annotation_data = create_annotation_data(rect, page_num, phrase, link)

                        if annotation_data:  # Only add if it's not a duplicate
                            all_annotations.append(annotation_data)

            # Flexible regex-based matching
            if not matched:
                flexible_pattern = re.escape(phrase).replace(r'\-', r'\-\s*').replace(r'\,', r'\,\s*')

                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    page_text = page.get_text("text")

                    for match in re.finditer(flexible_pattern, page_text, re.IGNORECASE):
                        matched = True
                        start, end = match.span()
                        match_text = page_text[start:end]
                        lines = match_text.splitlines()

                        for line in lines:
                            quads = page.search_for(line)
                            for quad in quads:
                                rect = fitz.Rect(quad)
                                annotation_data = create_annotation_data(rect, page_num, phrase, link)

                                if annotation_data:  # Only add if it's not a duplicate
                                    all_annotations.append(annotation_data)

            # Log phrase matches
            phrase_matches.append({'Document': pdf_file, 'Phrase': phrase, 'Matched': 'Yes' if matched else 'No'})

        # Save annotations to output using pandas
        if all_annotations:
            combined_annotations = "\\u0013".join([json.dumps(annotation).replace('"', '\\"') for annotation in all_annotations])
            annotation_json = f"{{\"Highlights\":\"{combined_annotations}\"}}"

            annotation_data_list.append({
                'Bates/Control #': pdf_file,
                'Annotation Data': annotation_json
            })

        # Save phrase matches using pandas
        for match in phrase_matches:
            phrase_matches_list.append(match)

        doc.close()

# Write the data to CSV files using pandas
annotation_df = pd.DataFrame(annotation_data_list)
phrase_matches_df = pd.DataFrame(phrase_matches_list)

# Write the DataFrames to CSV
annotation_df.to_csv(annotation_output_csv, index=False, encoding='utf-8')
phrase_matches_df.to_csv(phrases_output_csv, index=False, encoding='utf-8')
