# v0.1.0

import csv
import os
import json

# Input file
input_file = r"C:\Users\Willi\Downloads\Annotation Test\Annotation creation\Input file.csv"

# Create output file path
base_name = os.path.splitext(os.path.basename(input_file))[0]
output_filename = f"{base_name}_AnnotationsExtracted.csv"
output_filepath = os.path.join(os.path.dirname(input_file), output_filename)

# Function to extract highlights and notes
def extract_annotations(row):
    annotations = []
    try:
        annotation_data = json.loads(row['Annotation Data'])
        if 'Highlights' in annotation_data:
            highlights = annotation_data['Highlights'].split('\u0013')

            for highlight in highlights:
                highlight_json = json.loads(highlight)
                bates_number = row['Bates/Control #']
                
                # Extract highlighted text
                highlighted_text = highlight_json.get('markedText', '')

                # Extract notes (if available)
                notes = ''
                if 'notes' in highlight_json:
                    notes_list = highlight_json['notes']
                    if notes_list:
                        notes = notes_list[0].get('text', '')

                # Append the extracted data as a row
                annotations.append({
                    'Bates/Control #': bates_number,
                    'Highlighted Text': highlighted_text,
                    'Notes Text': notes
                })
    except json.JSONDecodeError as e:
        print(f"JSON error in row: {row['Bates/Control #']} - {e}")
    return annotations

# List to store extracted annotation data
extracted_data = []

# Read input CSV and extract annotations
with open(input_file, newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)

    for row in reader:
        if 'Annotation Data' in row and row['Annotation Data']:
            extracted_data.extend(extract_annotations(row))

# Write extracted data to a new CSV file
with open(output_filepath, mode='w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['Bates/Control #', 'Highlighted Text', 'Notes Text']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader()
    writer.writerows(extracted_data)

print(f"Done! Extracted annotations saved to: {output_filepath}")
