import csv
import json
import os

# Input file paths
input_file = r"your_input_annotations.csv"  # Replace with your input CSV or text file path

# Output file path
output_csv = r"filtered_annotations_output.csv"  # Replace with your desired output file path

# Email to exclude
exclude_user = "trial.solutions@advancediscovery.io"

# Dictionary to store annotation data by user
annotations_by_user = {}

# Determine delimiter based on file extension
input_delimiter = '\t' if input_file.endswith('.txt') else ','

# Read and parse the input file
with open(input_file, newline='', encoding='utf-8') as file:
    reader = csv.DictReader(file, delimiter=input_delimiter)
    for row in reader:
        # Assuming `user`, `markedText`, and other relevant fields are present in the input
        user = row['user']
        annotation_data = {
            "rectangles": row['rectangles'],
            "pageNum": row['pageNum'],
            "color": row['color'],
            "created": row['created'],
            "updated": row['updated'],
            "notes": row['notes'],
            "markedText": row['markedText']
        }
        
        # Store data if the user is not the excluded user
        if user != exclude_user:
            if user not in annotations_by_user:
                annotations_by_user[user] = []
            annotations_by_user[user].append(annotation_data)

# Prepare data for CSV output
filtered_data = []
for user, annotations in annotations_by_user.items():
    for annotation in annotations:
        # Flatten annotation data for CSV
        flattened_annotation = {
            'user': user,
            'rectangles': annotation['rectangles'],
            'pageNum': annotation['pageNum'],
            'color': annotation['color'],
            'created': annotation['created'],
            'updated': annotation['updated'],
            'notes': annotation['notes'],
            'markedText': annotation['markedText']
        }
        filtered_data.append(flattened_annotation)

# Write filtered annotations to a new CSV file
with open(output_csv, mode='w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['user', 'rectangles', 'pageNum', 'color', 'created', 'updated', 'notes', 'markedText']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    # Write the header
    writer.writeheader()

    # Write filtered annotation data
    for row in filtered_data:
        writer.writerow(row)

print(f"Filtered annotations saved to {output_csv}")
