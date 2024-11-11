import csv
import os
import json

# Input file
input_file = r"C:\Users\Willi\Downloads\Annotation Test\Annotation creation\Input file.csv"

# Output file creation
base_name = os.path.splitext(os.path.basename(input_file))[0]  
output_filename = f"{base_name}_FilteredAnnotationData.csv"
output_filepath = os.path.join(os.path.dirname(input_file), output_filename)  

# List to store the modified data
modified_data = []

# Define the user to filter out
user_to_filter = 'trial.solutions@advancediscovery.io'

# Prompt the user to select filter criteria
print("Choose your filter criteria:")
print("1: Filter by user email")
print("2: Filter by page range")
print("3: Filter by both")
choice = input("Enter your choice (1, 2, or 3): ")

# Set filter flags based on user choice
if choice == '1':
    filter_user = True
    filter_page_range = False
elif choice == '2':
    filter_user = False
    filter_page_range = True
elif choice == '3':
    filter_user = True
    filter_page_range = True
else:
    print("Invalid choice. Exiting.")
    exit()

# User filter: find or exclude
if filter_user:
    user_filter_choice = input("Do you want to find (include) or exclude this user email? (Enter 'find' or 'exclude'): ").strip().lower()
    include_user = user_filter_choice == 'find'

# Page range filter: find or exclude
if filter_page_range:
    page_range_input = input("Enter the page range (e.g., 1 - 50): ")
    start_page, end_page = [int(page.strip()) - 1 for page in page_range_input.split('-')]
    page_filter_choice = input("Do you want to find (include) or exclude this page range? (Enter 'find' or 'exclude'): ").strip().lower()
    include_page_range = page_filter_choice == 'find'

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
                    highlights = annotation_data['Highlights'].split('\u0013')  # Split using the separator
                    
                    # Filter highlights based on selected criteria
                    filtered_highlights = []
                    for highlight in highlights:
                        highlight_json = json.loads(highlight)  # Parse each highlight as JSON
                        
                        # Apply user filter
                        include_highlight = True
                        if filter_user:
                            user_matches = highlight_json.get('user') == user_to_filter
                            include_highlight = (user_matches if include_user else not user_matches)
                        
                        # Apply page range filter
                        if filter_page_range:
                            page_num = highlight_json.get('pageNum')
                            page_in_range = page_num is not None and (start_page <= page_num <= end_page)
                            include_highlight = include_highlight and (page_in_range if include_page_range else not page_in_range)
                        
                        # Add highlight if it meets criteria
                        if include_highlight:
                            filtered_highlights.append(highlight_json)

                    # Rebuild the Highlights string for Everlaw format
                    annotation_data['Highlights'] = '\u0013'.join(json.dumps(h, ensure_ascii=False) for h in filtered_highlights)

                # Store the modified annotation data back into the row
                row['Annotation Data'] = json.dumps(annotation_data, ensure_ascii=False)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")

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
