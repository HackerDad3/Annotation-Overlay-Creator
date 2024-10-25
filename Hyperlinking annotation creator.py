import fitz  # PyMuPDF
import csv
import json
from time import time
import os

# Set the user email as a variable
user_email = "william@advancediscovery.io"

# File paths
input_csv = r"C:\Users\Willi\Downloads\Annotation Test\Annotation creation\Input file.csv"
pdf_file = r"C:\Users\Willi\Downloads\Annotation Test\Annotation creation\LAY.WCH.001.0001.pdf"

# Get the directory of the input CSV file
input_directory = os.path.dirname(input_csv)

# Get the base name of the PDF without the extension
pdf_filename_no_ext = os.path.splitext(os.path.basename(pdf_file))[0]

# Construct the output CSV file path using the PDF name
output_csv = os.path.join(input_directory, f"{pdf_filename_no_ext}_annotation_output.csv")

# Open the PDF file
doc = fitz.open(pdf_file)

# Create an empty list to store all annotation data in the final format
all_annotations = []

# Function to generate the escaped JSON string for annotation data
def create_annotation_data(rectangles, page_num, phrase, link, user=user_email):
    timestamp = int(time() * 1000)  # Current time in milliseconds
    
    # Build the annotation data
    annotation_data = {
        "rectangles": {
            "rectangles": [{
                "x": rectangles.x0,
                "y": rectangles.y0,
                "width": rectangles.width,
                "height": rectangles.height
            }],
            "pageNum": page_num + 1,
            "color": "BLUE"
        },
        "created": timestamp,
        "updated": None,
        "notes": [{"text": f"<p>{link}</p>"}],
        "id": int(timestamp / 1000),
        "user": user,
        "unit": "point",
        "markedText": phrase
    }

    # Convert to JSON string and escape double quotes
    return json.dumps(annotation_data).replace('"', '\\"')

# Read the target phrases and their links from the input CSV
with open(input_csv, newline='') as csvfile:
    reader = csv.DictReader(csvfile)

    # For each row in the CSV (each phrase-link pair)
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
                    rect = fitz.Rect(inst)  # Bounding box as a rectangle object
                    annotation_data = create_annotation_data(rect, page_num, phrase, link)
                    all_annotations.append(annotation_data)

# Combine all the annotations into the final JSON annotation group
if all_annotations:
    combined_annotations = "\\u0013".join(all_annotations)
    annotation_json = f"{{\"Highlights\":\"{combined_annotations}\"}}"

    # Prepare the output CSV row
    output_data = {
        'Begin Bates': pdf_filename_no_ext,
        'Annotation Data': annotation_json
    }

    # Save the annotation data to the output CSV
    with open(output_csv, mode='w', newline='') as csvfile:
        fieldnames = ['Begin Bates', 'Annotation Data']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Write the header
        writer.writeheader()

        # Write the single annotation group to the CSV
        writer.writerow(output_data)

# Close the PDF document
doc.close()
