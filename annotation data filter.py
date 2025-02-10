import os
import json
import pandas as pd
import time

# Input file path
csv_file = input("Paste CSV filepath: ").strip().strip('"')
input_file = os.path.normpath(csv_file)

# Create the output file path
base_name = os.path.splitext(os.path.basename(input_file))[0]
output_filename = f"{base_name}_FilteredAnnotations.csv"
output_filepath = os.path.join(os.path.dirname(input_file), output_filename)

# Step 1: Ask how to filter the data
print("Choose your filter criteria:")
print("1: Filter by user email")
print("2: Filter by page range")
print("3: Filter by both")
print("4: No filtering")
choice = input("Enter your choice (1, 2, 3, or 4): ")

# Initialize flags
filter_user = filter_page_range = deduplicate_notes = update_timestamp = False
include_user = include_page_range = True

# Step 2: If filtering by user, get the email and choice to include/exclude
if choice in ('1', '3'):
    filter_user = True
    user_to_filter = input("Enter the user email to filter: ").strip()
    print("Do you want to include or exclude this user?")
    print("1: Include")
    print("2: Exclude")
    user_filter_choice = input("Enter your choice (1 or 2): ").strip()
    include_user = user_filter_choice == '1'

# Step 3: If filtering by page range, get the range and choice to include/exclude
if choice in ('2', '3'):
    filter_page_range = True
    # Subtracting 1 to work with zero-indexed page numbers (assumes JSON pageNum is zero-indexed)
    start_page = int(input("Enter the start page number: ")) - 1
    end_page = int(input("Enter the end page number: ")) - 1
    print("Do you want to include or exclude this page range?")
    print("1: Include")
    print("2: Exclude")
    page_filter_choice = input("Enter your choice (1 or 2): ").strip()
    include_page_range = page_filter_choice == '1'
    
    # Additional option for resetting page numbering within the filtered range
    print("Do you want to reset the page numbering for the filtered pages?")
    print("1: Do not reset (keep original page numbers)")
    print("2: Reset numbering to start at 0")
    print("3: Reset numbering to start at the beginning of the range (as entered)")
    page_reset_choice = input("Enter your choice (1, 2, or 3): ").strip()

# Step 4: Ask if the user wants to deduplicate text within the notes
print("Do you want to deduplicate text within the notes? (y/n)")
deduplicate_notes = input("Enter your choice: ").lower() == 'y'

# Step 5: Ask if the user wants to update the timestamps
print("Do you want to update the 'created' and 'updated' fields to the current datetime? (y/n)")
update_timestamp = input("Enter your choice: ").lower() == 'y'

# Read the CSV file using Pandas
df = pd.read_csv(input_file, encoding='utf-8')

# Check if the required column exists
if 'Annotation Data' not in df.columns:
    raise ValueError("The input CSV file does not contain the required 'Annotation Data' column.")

# Function to deduplicate text within notes
def deduplicate_note_text(note_text):
    """Deduplicate lines within the text, separated by <br>."""
    note_text = note_text.replace('<br><br>', '<br>').strip()
    has_p_tags = note_text.startswith('<p>') and note_text.endswith('</p>')
    if has_p_tags:
        note_text = note_text[3:-4].strip()
    lines = note_text.split('<br>')
    unique_lines = list(dict.fromkeys(line.strip() for line in lines if line.strip()))
    deduplicated_text = '<br>'.join(unique_lines)
    return f"<p>{deduplicated_text}</p>" if has_p_tags else deduplicated_text + '<br>'

# Function to update timestamps
def update_datetime_to_current(data):
    """Update 'created' and 'updated' timestamps to current datetime in milliseconds."""
    current_timestamp = int(time.time() * 1000)

    # Update top-level 'created' and 'updated' fields
    if 'created' in data:
        data['created'] = current_timestamp
    if 'updated' in data:
        data['updated'] = current_timestamp

    # Update nested 'created' in notes if present
    if 'notes' in data:
        for note in data['notes']:
            if 'created' in note:
                note['created'] = current_timestamp
    return data

# List to store the modified data
modified_data = []

# Iterate over each row in the DataFrame
for index, row in df.iterrows():
    if pd.notna(row['Annotation Data']):
        try:
            annotation_data = json.loads(row['Annotation Data'])

            # If 'Highlights' are present, filter them
            if 'Highlights' in annotation_data:
                highlights = annotation_data['Highlights'].split('\u0013')
                filtered_highlights = []

                for highlight in highlights:
                    highlight_json = json.loads(highlight)
                    include_highlight = True

                    # Filter by user email
                    if filter_user:
                        user_matches = highlight_json.get('user') == user_to_filter
                        if include_user:
                            include_highlight &= user_matches
                        else:
                            include_highlight &= not user_matches

                    # Filter by page range
                    if filter_page_range:
                        page_num = highlight_json.get('rectangles', {}).get('pageNum')
                        page_in_range = page_num is not None and (start_page <= page_num <= end_page)
                        if include_page_range:
                            include_highlight &= page_in_range
                        else:
                            include_highlight &= not page_in_range

                    # If the highlight is included and it has a page number,
                    # update the page numbering if the reset option was chosen.
                    if filter_page_range and include_highlight:
                        # Ensure we have a page number to work with
                        page_num = highlight_json.get('rectangles', {}).get('pageNum')
                        if page_num is not None:
                            if page_reset_choice == '2':
                                # Option 2: Reset numbering so that the first page in range becomes 0.
                                highlight_json['rectangles']['pageNum'] = page_num - start_page
                            elif page_reset_choice == '3':
                                # Option 3: Reset numbering so that the first page in range becomes what was entered.
                                # Since start_page was set to (entered start page - 1), this transformation makes:
                                #   if page_num == start_page then new value = (start_page - start_page) + (start_page+1) = start_page+1.
                                highlight_json['rectangles']['pageNum'] = page_num - start_page + (start_page + 1)

                    # Deduplicate text within the notes
                    if deduplicate_notes and 'notes' in highlight_json:
                        for note in highlight_json['notes']:
                            if 'text' in note and note['text']:
                                note['text'] = deduplicate_note_text(note['text'])

                    # Update timestamps if the option is enabled
                    if update_timestamp:
                        highlight_json = update_datetime_to_current(highlight_json)

                    if include_highlight:
                        filtered_highlights.append(highlight_json)

                annotation_data['Highlights'] = '\u0013'.join(
                    json.dumps(h, ensure_ascii=False) for h in filtered_highlights
                )

            # Update the row with the modified annotation data
            if update_timestamp:
                annotation_data = update_datetime_to_current(annotation_data)

            df.at[index, 'Annotation Data'] = json.dumps(annotation_data, ensure_ascii=False)
        except json.JSONDecodeError as e:
            print(f"JSON error in row {row.get('Bates/Control #', 'Unknown')} - {e}")

# Save the filtered data to a new CSV file
df.to_csv(output_filepath, index=False, encoding='utf-8')

print(f"Done! Processed annotations saved to: {output_filepath}")
