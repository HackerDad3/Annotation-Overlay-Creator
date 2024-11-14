import os
import json
import pandas as pd

# Input file path
input_file = r"C:\Users\Willi\Downloads\20241114T1138_UTC8_LAY.JOH.008.0001_current_annotation_data.csv"

# Create the output file path
base_name = os.path.splitext(os.path.basename(input_file))[0]
output_filename = f"{base_name}_FilteredAnnotations.csv"
output_filepath = os.path.join(os.path.dirname(input_file), output_filename)

# Ask user how they want to filter the data
print("Choose your filter criteria:")
print("1: Filter by user email")
print("2: Filter by page range")
print("3: Filter by both")
print("4: No filtering")
choice = input("Enter your choice (1, 2, 3, or 4): ")

# Flags for filtering
filter_user = filter_page_range = deduplicate_notes = False
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
    start_page = int(input("Enter the start page number: ")) - 1
    end_page = int(input("Enter the end page number: ")) - 1
    print("Do you want to include or exclude this page range?")
    print("1: Include")
    print("2: Exclude")
    page_filter_choice = input("Enter your choice (1 or 2): ").strip()
    include_page_range = page_filter_choice == '1'

# Ask if the user wants to deduplicate text within the notes
print("Do you want to deduplicate text within the notes? (y/n)")
deduplicate_notes = input("Enter your choice: ").lower() == 'y'

# Read the CSV file using Pandas
df = pd.read_csv(input_file, encoding='utf-8')

# Check if the required column exists
if 'Annotation Data' not in df.columns:
    raise ValueError("The input CSV file does not contain the required 'Annotation Data' column.")

# Function to deduplicate text within notes
def deduplicate_note_text(note_text):
    """ Deduplicate lines within the text, separated by <br>. """
    # Step 1: Normalize consecutive <br> tags
    note_text = note_text.replace('<br><br>', '<br>').strip()
    
    # Step 2: Check for leading <p> and trailing </p> tags
    has_p_tags = note_text.startswith('<p>') and note_text.endswith('</p>')
    if has_p_tags:
        # Remove the <p> and </p> tags for easier deduplication
        note_text = note_text[3:-4].strip()
    
    # Step 3: Split the text by <br>
    lines = note_text.split('<br>')
    
    # Step 4: Remove duplicates while preserving order, and strip spaces
    unique_lines = list(dict.fromkeys(line.strip() for line in lines if line.strip()))
    
    # Step 5: Join the unique lines back with <br>
    deduplicated_text = '<br>'.join(unique_lines)
    
    # Step 6: Re-add <p> and </p> tags if they were originally present
    if has_p_tags:
        deduplicated_text = f"<p>{deduplicated_text}</p>"
    
    # Ensure there is a single trailing <br>
    return deduplicated_text + '<br>'

# List to store the modified data
modified_data = []

# Iterate over each row in the DataFrame
for index, row in df.iterrows():
    if pd.notna(row['Annotation Data']):
        try:
            # Parse the JSON in the 'Annotation Data' field
            annotation_data = json.loads(row['Annotation Data'])

            # If 'Highlights' are present, filter them
            if 'Highlights' in annotation_data:
                highlights = annotation_data['Highlights'].split('\u0013')
                filtered_highlights = []

                # Go through each highlight
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

                    # Deduplicate text within the notes if the option is enabled
                    if deduplicate_notes and 'notes' in highlight_json:
                        for note in highlight_json['notes']:
                            if 'text' in note and note['text']:
                                # Deduplicate the text content within the note
                                note['text'] = deduplicate_note_text(note['text'])

                    # Add the highlight if it passes all filters
                    if include_highlight:
                        filtered_highlights.append(highlight_json)

                # Rebuild the Highlights string with the filtered highlights
                annotation_data['Highlights'] = '\u0013'.join(
                    json.dumps(h, ensure_ascii=False) for h in filtered_highlights
                )

            # Update the row with the modified annotation data
            df.at[index, 'Annotation Data'] = json.dumps(annotation_data, ensure_ascii=False)
        except json.JSONDecodeError as e:
            print(f"JSON error in row {row.get('Bates/Control #', 'Unknown')} - {e}")

# Save the filtered data to a new CSV file
df.to_csv(output_filepath, index=False, encoding='utf-8')

print(f"Done! Processed annotations saved to: {output_filepath}")
