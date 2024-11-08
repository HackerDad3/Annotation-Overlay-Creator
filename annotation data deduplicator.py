import csv
import os
import json

# Input file
input_file = r"C:\Users\Willi\Downloads\Annotation Test\Annotation creation\Input file.csv"

# Output file creation. I hate pasting file paths all the time.
base_name = os.path.splitext(os.path.basename(input_file))[0] 
output_filename = f"{base_name}_Deduplicated.csv"  
output_filepath = os.path.join(os.path.dirname(input_file), output_filename)  

# List to store the modified data
modified_data = []

# Open the CSV for reading
with open(input_file, newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)

    # Iterate over each row in the CSV
    for row in reader:
        if 'Annotation Data' in row and row['Annotation Data']:
            try:
                # Parse the original Everlaw JSON data
                annotation_data = json.loads(row['Annotation Data'])

                # Check if 'Highlights' is present
                if 'Highlights' in annotation_data:
                    # Split the highlights based on the custom delimiter used in your data
                    highlights = annotation_data['Highlights'].split('\u0013')

                    # Use a set to track unique highlights based on their string representation
                    unique_highlights = set()
                    deduplicated_highlights = []

                    for highlight in highlights:
                        highlight_json = json.loads(highlight)  # Parse each highlight as JSON
                        # Create a string representation of the highlight for comparison
                        highlight_str = json.dumps(highlight_json, sort_keys=True, ensure_ascii=False)

                        # Check if this string representation is already in the set
                        if highlight_str not in unique_highlights:
                            unique_highlights.add(highlight_str)  # Add to unique highlights
                            deduplicated_highlights.append(highlight_json)  # Add to the deduplicated list

                    # Rebuild the Highlights string for Everlaw format
                    annotation_data['Highlights'] = '\u0013'.join(json.dumps(h, ensure_ascii=False) for h in deduplicated_highlights)

                # Store the modified annotation data back into the row
                row['Annotation Data'] = json.dumps(annotation_data, ensure_ascii=False)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")

        # Append the modified row to the list
        modified_data.append(row)

# Not needed.  used in json testing.
# # Print the first modified row for verification
# print(f"First modified row: {modified_data[0] if modified_data else 'No data found'}")

# Save the modified data to a new CSV file
with open(output_filepath, mode='w', newline='', encoding='utf-8') as csvfile:
    fieldnames = reader.fieldnames  # Use the original fieldnames from the input file
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    # Write the header
    writer.writeheader()

    # Write the modified data rows
    for row in modified_data:
        writer.writerow(row)

print(f"Processed annotations saved to: {output_filepath}")
