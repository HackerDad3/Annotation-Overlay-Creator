import csv
import os
import json

# Input file
input_file = r"C:\Users\Willi\Downloads\Annotation Test\Annotation creation\Input file.csv"

# Output file creation so I don't have to paste all the time
base_name = os.path.splitext(os.path.basename(input_file))[0]  
output_filename = f"{base_name}_FilteredAnnotations.csv"
output_filepath = os.path.join(os.path.dirname(input_file), output_filename)  

# List to store the modified data
modified_data = []

# Prompt the user to select filter criteria.  This is first draft of prompts
print("Choose your filter criteria:")
print("1: Filter by user email")
print("2: Filter by page range")
print("3: Filter by both")
choice = input("Enter your choice (1, 2, or 3): ")

# Variables for filter options
filter_user = filter_page_range = False
include_user = include_page_range = True  # Make it default.  It worked this way

# Configure user email filter
if choice in ('1', '3'):
    filter_user = True
    user_to_filter = input("Enter the user email to filter: ")
    user_filter_choice = input("Do you want to include or exclude this user? (Enter 'include' or 'exclude'): ").strip().lower()
    include_user = user_filter_choice == 'include'

# Configure page range filter
if choice in ('2', '3'):
    filter_page_range = True
    start_page = int(input("Enter the start page number: ")) - 1  # Adjust for 0-based index
    end_page = int(input("Enter the end page number: ")) - 1      # Adjust for 0-based index
    page_filter_choice = input("Do you want to include or exclude this page range? (Enter 'include' or 'exclude'): ").strip().lower()
    include_page_range = page_filter_choice == 'include'

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
                    
                    # Filter highlights based on selected criteria
                    filtered_highlights = []
                    for highlight in highlights:
                        highlight_json = json.loads(highlight)  # Parse each highlight as JSON
                        
                        # Initialize inclusion for this highlight
                        include_highlight = True
                        
                        # Apply user email filter
                        if filter_user:
                            user_matches = highlight_json.get('user') == user_to_filter
                            if include_user:
                                include_highlight &= user_matches  # Include only if user matches
                            else:
                                include_highlight &= not user_matches  # Exclude if user matches
                        
                        # Apply page range filter
                        if filter_page_range:
                            page_num = highlight_json.get('rectangles', {}).get('pageNum')
                            page_in_range = page_num is not None and (start_page <= page_num <= end_page)
                            if include_page_range:
                                include_highlight &= page_in_range  # Include only if in range
                            else:
                                include_highlight &= not page_in_range  # Exclude if in range
                        
                        # Add highlight if it meets criteria
                        if include_highlight:
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
