import csv
import os
import json
import re
from time import time

# Input file
input_file = r"C:\Users\Willi\Downloads\Annotation Test\Annotation creation\annotations_output.csv"

# Output CSV file path
output_csv_file = os.path.join(os.path.dirname(input_file),f'{os.path.splitext(os.path.basename(input_file))[0]}_UserNotes.csv')

# List to store the modified data
modified_data = []
# List to store errors for debugging
debug_info = []

def clean_and_validate_json(annotation_data):
    """Cleans and validates the JSON format."""
    try:
        # Replace Everlaw format json \u0013, double " and \
        cleaned_data = annotation_data.replace(r'\u0013', ',')
        cleaned_data = cleaned_data.replace('\\', '')
        cleaned_data = cleaned_data.replace('""', '"')
        # Restructure highlights start to create good json
        cleaned_data = cleaned_data.replace('{"Highlights":"', '{"Highlights":[')
        cleaned_data = cleaned_data.replace('"}"}', '"}]}')
        
        # Attempt to parse the JSON to check if it's valid
        json_data = json.loads(cleaned_data)
        return json_data, None  # Return the parsed JSON and no error

    except json.JSONDecodeError as e:
        # Return None and the error message if parsing fails
        return None, str(e)

def filter_highlights(json_data):
    """Filters out highlights created by a specific user."""
    if 'Highlights' in json_data:
        # Retain only highlights not created by the specified user
        json_data['Highlights'] = [
            highlight for highlight in json_data['Highlights']
            if highlight.get('user') != 'trial.solutions@advancediscovery.io'
        ]
    return json_data

def create_annotation_data(rectangles, page_num, phrase, user, created):
    """Creates annotation data in the original format."""
    return {
        "rectangles": {
            "rectangles": [
                {
                    "x": rectangles['x'],
                    "y": rectangles['y'],
                    "width": rectangles['width'],
                    "height": rectangles['height']
                }
            ],
            "pageNum": page_num,
            "color": "BLUE"
        },
        "created": created,
        "updated": created,
        "notes": [
            {
                "text": f"<p>Link</p>",
                "created": created,
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

def reformat_annotation_data(json_data):
    """Reformats cleaned JSON back to the original string format."""
    highlights = json_data.get('Highlights', [])
    if highlights:
        formatted_highlights = []
        for highlight in highlights:
            rects = highlight["rectangles"]["rectangles"][0]
            created = highlight["created"]
            user = highlight["user"]
            phrase = highlight["markedText"]
            
            annotation_data = create_annotation_data(
                rectangles={
                    'x': rects["x"],
                    'y': rects["y"],
                    'width': rects["width"],
                    'height': rects["height"]
                },
                page_num=highlight["rectangles"]["pageNum"],
                phrase=phrase,
                user=user,
                created=created
            )
            formatted_highlights.append(annotation_data)
        
        return {"Highlights": formatted_highlights}
    return {}

# Open the CSV for reading
with open(input_file, newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)

    # Iterate over each row in the CSV and save to the list
    for row in reader:
        if 'Annotation Data' in row and row['Annotation Data']:
            json_data, error = clean_and_validate_json(row['Annotation Data'])
            if json_data is not None:
                # Filter highlights before appending to modified data
                filtered_json_data = filter_highlights(json_data)
                # Reformat filtered JSON back to the original style
                original_format_data = reformat_annotation_data(filtered_json_data)
                row['Annotation Data'] = json.dumps(original_format_data, ensure_ascii=False)
            else:
                debug_info.append({
                    'original': row['Annotation Data'],
                    'error': error
                })

        # Append the modified row to the list
        modified_data.append(row)

# Print the first modified row for verification
print(f"First modified row: {modified_data[0] if modified_data else 'No data found'}")

# Print debug information if there were any issues
if debug_info:
    print("Errors found in the following annotations:")
    for info in debug_info:
        print(f"Original: {info['original']}\nError: {info['error']}\n")
else:
    print("All annotations are formatted correctly.")

# Save the modified data to a new CSV file
with open(output_csv_file, mode='w', newline='', encoding='utf-8') as csvfile:
    fieldnames = reader.fieldnames  # Use the original fieldnames from the input file
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    # Write the header
    writer.writeheader()

    # Write the modified data rows
    for row in modified_data:
        writer.writerow(row)

print(f"Processed annotations saved to: {output_csv_file}")
