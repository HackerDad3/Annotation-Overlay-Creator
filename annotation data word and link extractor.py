import pandas as pd
import os
import re

# Input file path
input_file = r"C:\Users\Willi\Downloads\20241112T1208_UTC8_Lay_Notes_Full.csv"

# Create output file path automatically
base_name = os.path.splitext(os.path.basename(input_file))[0]
output_filename = f"{base_name}_ExtractedNotes.csv"
output_file = os.path.join(os.path.dirname(input_file), output_filename)

def process_notes(note_text):
    """Split the notes using double line breaks."""
    if pd.isna(note_text):
        return []
    notes = [note.strip() for note in note_text.split('\n\n') if note.strip()]
    return notes

def extract_document_info(note):
    """Extract Document ID and Filename from the Note Text."""
    match = re.match(r"^(\S+)\s+\((.+)\)$", note)
    if match:
        document_id = match.group(1)
        filename = match.group(2)
        return document_id, filename
    return None, None

# Read the input CSV using Pandas
df = pd.read_csv(input_file, encoding='utf-8-sig')

# Check if the required columns exist
if 'Bates/Control #' not in df.columns or 'Note Text' not in df.columns:
    raise ValueError("Input file is missing required columns: 'Bates/Control #' or 'Note Text'")

# Create an empty DataFrame to store the processed notes
output_data = []

# Process each row to split the notes and extract Document ID and Filename
for _, row in df.iterrows():
    bates_number = row['Bates/Control #']
    note_text = row['Note Text']
    
    # Split the notes
    notes = process_notes(note_text)
    for note in notes:
        document_id, filename = extract_document_info(note)
        output_data.append({
            'Bates/Control #': bates_number,
            'Note Text': note,
            'Document ID': document_id,
            'Filename': filename
        })

# Convert the processed data into a DataFrame
output_df = pd.DataFrame(output_data)

# Write the output DataFrame to a CSV file
output_df.to_csv(output_file, index=False, encoding='utf-8')

print(f"Done! Extracted notes saved to: {output_file}. So long and thanks for all the fish!!")
