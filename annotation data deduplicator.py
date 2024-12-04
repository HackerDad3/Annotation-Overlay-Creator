import os
import json
import pandas as pd

# Input file path
# input_file = r"C:\Users\Willi\Downloads\Annotation Test\Annotation creation\Input file.csv"
input_csv = input("Paste CSV file path here: ")

# normalise path
input_file = os.path.normpath(input_csv)

# Output file creation
base_name = os.path.splitext(os.path.basename(input_file))[0]
output_filename = f"{base_name}_Deduplicated.csv"
output_filepath = os.path.join(os.path.dirname(input_file), output_filename)

# Define the keys to consider for deduplication if filtering is enabled
keys_to_check = ['pageNum', 'highlightedText', 'text', 'notes.text']

# Set this flag to True if you want to filter by specific keys, False to use all keys
use_filtered_keys = True  # Change this to False if you want to deduplicate on all keys

# Helper function to get nested key values using dot notation
def get_nested_value(data, key):
    """
    Retrieve a nested value from a dictionary using a dot-separated key.
    """
    keys = key.split('.')
    for k in keys:
        if isinstance(data, dict) and k in data:
            data = data[k]
        else:
            return None
    return data

# Function to extract relevant fields for deduplication
def extract_keys(data, keys_to_check):
    """
    Extracts specified keys from a dictionary, including nested keys.
    """
    filtered_data = {}
    for key in keys_to_check:
        value = get_nested_value(data, key)
        if value is not None:
            filtered_data[key] = value
    return filtered_data

# Read the CSV file using pandas
df = pd.read_csv(input_file, encoding='utf-8')

# Check if the required column 'Annotation Data' exists
if 'Annotation Data' not in df.columns:
    raise ValueError("The input CSV file does not contain the required 'Annotation Data' column.")

# List to store modified rows
modified_data = []

# Iterate over each row in the DataFrame
for index, row in df.iterrows():
    if pd.notna(row['Annotation Data']):
        try:
            # Parse the original Everlaw JSON data
            annotation_data = json.loads(row['Annotation Data'])

            # Check if 'Highlights' is present
            if 'Highlights' in annotation_data:
                # Split the highlights based on the custom delimiter used in your data
                highlights = annotation_data['Highlights'].split('\u0013')

                # Use a set to track unique highlights
                unique_highlights = set()
                deduplicated_highlights = []

                for highlight in highlights:
                    highlight_json = json.loads(highlight)  # Parse each highlight as JSON

                    # Determine the string representation for deduplication
                    if use_filtered_keys:
                        # Extract only the specified keys (including nested keys)
                        filtered_highlight = extract_keys(highlight_json, keys_to_check)
                        highlight_str = json.dumps(filtered_highlight, sort_keys=True, ensure_ascii=False)
                    else:
                        # Use all keys in the dictionary for deduplication
                        highlight_str = json.dumps(highlight_json, sort_keys=True, ensure_ascii=False)

                    # Check if this representation is already in the set
                    if highlight_str not in unique_highlights:
                        unique_highlights.add(highlight_str)  # Add to unique highlights
                        deduplicated_highlights.append(highlight_json)  # Add the original highlight

                # Rebuild the Highlights string for Everlaw format
                annotation_data['Highlights'] = '\u0013'.join(
                    json.dumps(h, ensure_ascii=False) for h in deduplicated_highlights
                )

            # Store the modified annotation data back into the DataFrame
            df.at[index, 'Annotation Data'] = json.dumps(annotation_data, ensure_ascii=False)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON for row {index}: {e}")

# Save the modified DataFrame to a new CSV file
df.to_csv(output_filepath, index=False, encoding='utf-8')

print(f"Processed annotations saved to: {output_filepath}")
