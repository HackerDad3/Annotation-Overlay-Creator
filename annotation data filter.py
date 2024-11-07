import csv
import os
import json

# Input file
input_file = r"C:\Users\Willi\Downloads\Annotation Test\Annotation creation\Input file.csv"

# Output file creation
base_name = os.path.splitext(os.path.basename(input_file))[0]  
output_filename = f"{base_name}_UserNotes.csv"
output_filepath = os.path.join(os.path.dirname(input_file), output_filename)  

# List to store the modified data
modified_data = []

# Define the user to filter out. Never William though.  He's the best. 
user_to_filter = 'trial.solutions@advancediscovery.io'

# Open the CSV for reading
with open(input_file, newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)

    # Iterate over each row in the CSV
    for row in reader:
        if 'Annotation Data' in row and row['Annotation Data']:
            try:
                # Parse the original Everlaw JSON data
                annotation_data = json.loads(row['Annotation Data'])
                
                # Check if 'Highlights' is present. Pretty sure it always is.
                if 'Highlights' in annotation_data:
                    highlights = annotation_data['Highlights'].split('\u0013')  # Split using the separator
                    
                    # Filter out highlights created by the specified user
                    filtered_highlights = []
                    for highlight in highlights:
                        highlight_json = json.loads(highlight)  # Parse each highlight as JSON
                        if highlight_json.get('user') != user_to_filter:
                            filtered_highlights.append(highlight_json)

                    # Rebuild the Highlights string for Everlaw format
                    annotation_data['Highlights'] = '\u0013'.join(json.dumps(h, ensure_ascii=False) for h in filtered_highlights)

                # Store the modified annotation data back into the row
                row['Annotation Data'] = json.dumps(annotation_data, ensure_ascii=False)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")

        # Append the modified row to the list
        modified_data.append(row)

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
