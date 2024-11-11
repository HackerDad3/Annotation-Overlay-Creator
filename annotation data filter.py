import csv
import os
import json

# Input file
input_file = r"C:\Users\Willi\Downloads\Annotation Test\Annotation creation\Input file.csv"

# Output file creation
base_name = os.path.splitext(os.path.basename(input_file))[0]  
output_filename = f"{base_name}_FilteredByPageRange.csv"
output_filepath = os.path.join(os.path.dirname(input_file), output_filename)  

# List to store the modified data
modified_data = []

# Prompt for the page range to include
start_page = int(input("Enter the start page number: ")) - 1  # Adjust for 0-based index
end_page = int(input("Enter the end page number: ")) - 1      # Adjust for 0-based index

# Open the CSV for reading
with open(input_file, newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)

    # Iterate over each row in the CSV
    for row in reader:
        if 'Annotation Data' in row and row['Annotation Data']:
            try:
                # Parse the original JSON data in the 'Annotation Data' field
                annotation_data = json.loads(row['Annotation Data'])
                
                # Check if 'Highlights' is present
                if 'Highlights' in annotation_data:
                    highlights = annotation_data['Highlights'].split('\u0013')  # Split using the separator
                    
                    # Filter highlights based on the specified page range
                    filtered_highlights = []
                    for highlight in highlights:
                        highlight_json = json.loads(highlight)  # Parse each highlight as JSON
                        page_num = highlight_json.get('rectangles', {}).get('pageNum')

                        # Only include highlights within the specified page range
                        if page_num is not None and start_page <= page_num <= end_page:
                            filtered_highlights.append(highlight_json)

                    # Rebuild the Highlights string with only the filtered highlights
                    annotation_data['Highlights'] = '\u0013'.join(
                        json.dumps(h, ensure_ascii=False) for h in filtered_highlights
                    )

                # Store the modified annotation data back into the row
                row['Annotation Data'] = json.dumps(annotation_data, ensure_ascii=False)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON in row: {row['Bates/Control #']} - {e}")

        # Append the modified row to the list
        modified_data.append(row)

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
