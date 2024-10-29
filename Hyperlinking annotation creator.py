import fitz  # PyMuPDF
import csv
import json
from time import time
import os

# User email to show in notes
user_email = "william@advancediscovery.io"

# File paths
input_file = r"C:\Users\Willi\Downloads\Annotation Test\Annotation creation\Input file.csv"
pdf_file = r"C:\Users\Willi\Downloads\Annotation Test\Annotation creation\LAY.WCH.001.0001.pdf"

# Determine delimiter based on file extension
input_delimiter = '\t' if input_file.endswith('.txt') else ','

# Get the file name without extension for the "Bates/Control #" column
pdf_filename_no_ext = os.path.splitext(os.path.basename(pdf_file))[0]

# Open the PDF file
doc = fitz.open(pdf_file)

# Create an empty list to store all annotation data in the final format
all_annotations = []

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
    
    # Convert to a JSON string and escape it
    return json.dumps(annotation_data).replace('"', '\\"')

# Read the target phrases and their links from the input file
with open(input_file, newline='', encoding='utf-8') as file:
    reader = csv.DictReader(file, delimiter=input_delimiter)

    # For each row in the input file (each phrase-link pair)
    for row in reader:
        phrase = row['Phrase']
        link = row['Link']

        # Loop through each page in the PDF to find the phrase
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            
            # Search for the phrase on the page
            instances = page.search_for(phrase)
            
            if instances:
                # For each instance of the phrase found, generate annotation data
                for inst in instances:
                    rect = fitz.Rect(inst)  # bounding box as a rectangle object
                    annotation_data = create_annotation_data(rect, page_num, phrase, link)
                    all_annotations.append(annotation_data)

# Combine all the annotations into the final JSON annotation group
if all_annotations:
    combined_annotations = "\\u0013".join(all_annotations)
    annotation_json = f"{{\"Highlights\":\"{combined_annotations}\"}}"

    # Prepare the output CSV row
    output_data = {
        'Bates/Control #': pdf_filename_no_ext,
        'Annotation Data': annotation_json
    }

    # Save the annotation data to the output CSV
    output_csv = os.path.join(os.path.dirname(input_file), f"{pdf_filename_no_ext}_annotation_output.csv")
    with open(output_csv, mode='w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Bates/Control #', 'Annotation Data']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Write the header
        writer.writeheader()

        # Write the single annotation group to the CSV
        writer.writerow(output_data)

# Close the PDF document
doc.close()
