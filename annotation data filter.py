import csv
import os
import json

# Input file. This can probably be an input??
input_file = r"C:\Users\Willi\Downloads\Annotation Test\Annotation creation\Input file.csv"

# Just make the output file path so I don't have to copy-paste each time
base_name = os.path.splitext(os.path.basename(input_file))[0]  
output_filename = f"{base_name}_FilteredAnnotations.csv"
output_filepath = os.path.join(os.path.dirname(input_file), output_filename)  

# List to hold the modified data
modified_data = []

# Ask user how they wanna filter stuff
print("Choose your filter criteria:")
print("1: Filter by user email")
print("2: Filter by page range")
print("3: Filter by both")
choice = input("Enter your choice (1, 2, or 3): ")

# Flags for what we're filtering and default to include
filter_user = filter_page_range = False
include_user = include_page_range = True

# If filtering by user, get the email and choice to include/exclude
if choice in ('1', '3'):
    filter_user = True
    user_to_filter = input("Enter the user email to filter: ")
    print("Do you want to include or exclude this user?")
    print("1: Include")
    print("2: Exclude")
    user_filter_choice = input("Enter your choice (1 or 2): ").strip()
    include_user = user_filter_choice == '1'

# If filtering by page range, get the range and choice to include/exclude
if choice in ('2', '3'):
    filter_page_range = True
    start_page = int(input("Enter the start page number: ")) - 1  # 1-based to 0-based
    end_page = int(input("Enter the end page number: ")) - 1      # Adjust as above
    print("Do you want to include or exclude this page range?")
    print("1: Include")
    print("2: Exclude")
    page_filter_choice = input("Enter your choice (1 or 2): ").strip()
    include_page_range = page_filter_choice == '1'

# Open up the CSV and start reading
with open(input_file, newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)

    # Go through each row in the file
    for row in reader:
        if 'Annotation Data' in row and row['Annotation Data']:
            try:
                # Parse the JSON that's in the 'Annotation Data' field
                annotation_data = json.loads(row['Annotation Data'])
                
                # If 'Highlights' are there, we’re good get shit done
                if 'Highlights' in annotation_data:
                    highlights = annotation_data['Highlights'].split('\u0013')  # Split them up
                    
                    # Go through highlights and filter as needed
                    filtered_highlights = []
                    for highlight in highlights:
                        highlight_json = json.loads(highlight)  # Get each highlight as JSON
                        
                        # Start by assuming we'll keep it
                        include_highlight = True
                        
                        # Check if we need to filter by user email
                        if filter_user:
                            user_matches = highlight_json.get('user') == user_to_filter
                            if include_user:
                                include_highlight &= user_matches  # Only if user matches
                            else:
                                include_highlight &= not user_matches  # Exclude if user matches
                        
                        # Check if we need to filter by page range
                        if filter_page_range:
                            page_num = highlight_json.get('rectangles', {}).get('pageNum')
                            page_in_range = page_num is not None and (start_page <= page_num <= end_page)
                            if include_page_range:
                                include_highlight &= page_in_range  # Only if in range
                            else:
                                include_highlight &= not page_in_range  # Exclude if in range
                        
                        # Add highlight if it’s still good after all that
                        if include_highlight:
                            filtered_highlights.append(highlight_json)

                    # Rebuild Highlights with only the filtered ones
                    annotation_data['Highlights'] = '\u0013'.join(
                        json.dumps(h, ensure_ascii=False) for h in filtered_highlights
                    )

                # Put the modified JSON back in the row
                row['Annotation Data'] = json.dumps(annotation_data, ensure_ascii=False)
            except json.JSONDecodeError as e:
                print(f"JSON error in row: {row['Bates/Control #']} - {e}")

        # Add the row to our modified data list
        modified_data.append(row)

# Write out the new CSV with the filtered data
with open(output_filepath, mode='w', newline='', encoding='utf-8') as csvfile:
    fieldnames = reader.fieldnames  # Keep original fieldnames
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    # Write the header and the filtered data
    writer.writeheader()
    for row in modified_data:
        writer.writerow(row)

print(f"Done! Processed annotations saved to: {output_filepath}")
