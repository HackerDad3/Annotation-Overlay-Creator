import os
import json
import pandas as pd

def parse_annotation_data(annotation_data_str):
    """
    Given a JSON string from the 'Annotation Data' column, this function extracts
    each highlight's markedText and, for each note within the highlight, the note's text.
    
    Returns:
        A list of dictionaries with keys 'Reference' and 'Note'
    """
    parsed_rows = []
    try:
        annotation_data = json.loads(annotation_data_str)
    except json.JSONDecodeError as e:
        print(f"Error decoding annotation JSON: {e}")
        return parsed_rows

    # Check if the JSON data contains the 'Highlights' key
    if "Highlights" not in annotation_data:
        return parsed_rows

    # The 'Highlights' field is expected to be a string with individual highlight JSON strings
    # separated by the delimiter \u0013.
    highlights_str = annotation_data["Highlights"]
    if not highlights_str.strip():
        return parsed_rows  # nothing to parse if empty

    highlights = highlights_str.split("\u0013")
    
    for highlight_str in highlights:
        try:
            highlight = json.loads(highlight_str)
        except json.JSONDecodeError as e:
            print(f"Error decoding a highlight JSON segment: {e}")
            continue

        # Extract markedText for the highlight
        marked_text = highlight.get("markedText", "")
        
        # Check for notes (which should be a list) and extract the text from each note
        if "notes" in highlight and isinstance(highlight["notes"], list):
            for note in highlight["notes"]:
                note_text = note.get("text", "")
                parsed_rows.append({
                    "Reference": marked_text,
                    "Note": note_text
                })
        else:
            # If there are no notes, record the marked text with an empty note.
            parsed_rows.append({
                "Reference": marked_text,
                "Note": ""
            })
    return parsed_rows

def main():
    # Ask for the CSV file that was created by the previous script.
    input_csv = input("Enter the path to the CSV file created by the previous script: ").strip().strip('"')
    input_csv = os.path.normpath(input_csv)

    # Read the CSV file into a pandas DataFrame.
    df = pd.read_csv(input_csv, encoding='utf-8')

    all_parsed_rows = []
    # Process each row in the DataFrame
    for idx, row in df.iterrows():
        annotation_data_str = row.get("Annotation Data")
        if pd.isna(annotation_data_str):
            continue

        parsed_rows = parse_annotation_data(annotation_data_str)
        all_parsed_rows.extend(parsed_rows)

    # Create an output file path.
    base_name = os.path.splitext(os.path.basename(input_csv))[0]
    output_csv = os.path.join(os.path.dirname(input_csv), f"{base_name}_ParsedData.csv")

    # Create a DataFrame from the parsed rows and save it to CSV.
    parsed_df = pd.DataFrame(all_parsed_rows)
    parsed_df.to_csv(output_csv, index=False, encoding='utf-8')

    print(f"Parsed data saved to: {output_csv}")

if __name__ == "__main__":
    main()
