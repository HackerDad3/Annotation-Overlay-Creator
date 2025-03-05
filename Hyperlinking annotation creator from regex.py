import fitz  # PyMuPDF
import pandas as pd  # Import pandas for CSV processing
import json
import re
import zipfile
import io
from time import time
from tqdm import tqdm
import datetime
import os

# User email to show in notes
user_email = "trial.solutions@advancediscovery.io"

document_number = input("Main Document number: ")

# File paths
input_csv_file = input("Paste existing CSV file path with annotation data: ").strip().strip('"')
zip_file_path = input("Paste ZIP file path containing PDF files: ").strip().strip('"')

# Normalize paths
input_file = os.path.normpath(input_csv_file)
zip_file = os.path.normpath(zip_file_path)

# Output directory (same as input CSV file's directory)
output_dir = os.path.dirname(input_file)

current_date = datetime.datetime.now().strftime("%Y%m%d")

# Combined output file paths
annotation_output_csv = os.path.join(output_dir, f"{current_date}_{document_number}_updated_annotation_output.csv")

# Initialize the output data
annotation_data_list = []

# Load existing annotation data from the input CSV
existing_annotations = pd.read_csv(input_file)

# The regex pattern for searching the phrases in the PDF
regex_pattern = r"([A-Z]{3,5}\.\s*[A-Z0-9]{3,4}\.\s*[0-9]{3,4}\.\s*[0-9]{3,6}(_\d{4})?)|(Exhibit\s(PLE|CWS|CE|RE|CL|RL|TER|JER|CEX|REX|ORD|TRX)-\d{3,4}(_\d{4})?)|((PLE|CWS|CE|RE|CL|RL|TER|JER|CEX|REX|ORD|TRX)-\d{2,4}(_\d{4})?)|(REX-\d{3,4}\.\d{3,4}(_\d{4})?)|(Exhibit\s+(REX-\d{3,4}\.\d{3,4}(_\d{4})?))|((CC|RC|TC|JC)\.\d{3,4}[A-Z]?\.\d{3}(_\d{4})?)|(Exhibit\s+(CC|RC|TC|JC)\.\d{3,4}[A-Z]?\.\d{3}(_\d{4})?)"

# Function to generate the escaped JSON string for annotation data
def create_annotation_data(rectangles, page_num, phrase, user=user_email):
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
                "text": f"<p>{phrase}</p>",  # Matched phrase will be used in the note
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
    return annotation_data

# Open the zip file and process PDFs without extracting them
with zipfile.ZipFile(zip_file, 'r') as zip_ref:
    # List all PDF files in the zip file (including files in subdirectories)
    pdf_files = [f for f in zip_ref.namelist() if f.endswith('.pdf')]

    for pdf_file in tqdm(pdf_files, desc="Processing PDFs"):
        # Read the PDF file from the zip archive into memory
        with zip_ref.open(pdf_file) as file:
            file_data = file.read()

            # Open the PDF from memory using PyMuPDF (fitz)
            doc = fitz.open(io.BytesIO(file_data))
            new_annotations = []

            # Iterate over each row in the existing annotation CSV
            for _, row in tqdm(existing_annotations.iterrows(), desc=f"Processing annotations in {pdf_file}", total=existing_annotations.shape[0]):
                phrase = row['Marked Text']
                matched = False

                # Search for regex matches in the PDF
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    page_text = page.get_text("text")

                    for match in re.finditer(regex_pattern, page_text, re.IGNORECASE):
                        matched = True
                        start, end = match.span()
                        match_text = page_text[start:end]
                        lines = match_text.splitlines()

                        # For each matched line, generate an annotation
                        for line in lines:
                            quads = page.search_for(line)
                            for quad in quads:
                                rect = fitz.Rect(quad)
                                annotation_data = create_annotation_data(rect, page_num, match.group())

                                # Append the new annotation
                                new_annotations.append(annotation_data)

            # Add new annotations to the existing annotations list
            annotation_data_list.extend(new_annotations)

# Append newly created annotation data to the existing CSV
for annotation in annotation_data_list:
    existing_annotations = existing_annotations.append({
        'Bates/Control #': pdf_file,
        'Annotation Data': json.dumps(annotation),
        'Marked Text': annotation['markedText']
    }, ignore_index=True)

# Save the updated annotation data to the new CSV file
existing_annotations.to_csv(annotation_output_csv, index=False, encoding='utf-8')

