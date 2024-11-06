import csv
import os
import json

# Input file
input_file = r"C:\Users\Willi\Downloads\Annotation Test\Annotation creation\annotations_output.csv"

# Output file creation
base_name = os.path.splitext(os.path.basename(input_file))[0]  # Get the base name of the input file
output_filename = f"{base_name}_Filtered.csv"  # Format the output file name
output_filepath = os.path.join(os.path.dirname(input_file), output_filename)  # Create output path

# List to store the modified data
modified_data = []

# Open the CSV for reading
with open(input_file, newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)

    # Iterate over each row in the CSV and save to the list
    for row in reader:
        if 'Annotation Data' in row and row['Annotation Data']:
            # replace Everlaw format json \u0013, double " and \
            row['Annotation Data'] = row['Annotation Data'].replace(r'\u0013', ',')
            row['Annotation Data'] = row['Annotation Data'].replace('\\', '')
            row['Annotation Data'] = row['Annotation Data'].replace('""', '"')
            #resturcture highlights start to create good json
            row['Annotation Data'] = row['Annotation Data'].replace('{"Highlights":"','{"Highlights":[')
            row['Annotation Data'] = row['Annotation Data'].replace('"}"}', '"}]}')

        # Append the modified row to the list
        modified_data.append(row)

# Print the first modified row for verification
print(f"First modified row: {modified_data[0] if modified_data else 'No data found'}")

# Write the modified data back to a new CSV file
with open(output_filepath, mode='w', newline='', encoding='utf-8') as csvfile:
    fieldnames = modified_data[0].keys() if modified_data else []
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    # Write the header
    writer.writeheader()

    # Write the modified data
    for row in modified_data:
        writer.writerow(row)

print(f"Modified annotations saved to {output_filepath}")
