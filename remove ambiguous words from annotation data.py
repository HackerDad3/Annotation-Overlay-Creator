import pandas as pd
import os

def remove_rows_by_reference(input_csv, output_csv, remove_list):
    """
    Remove rows from a CSV file where the 'Reference' column exactly matches specific words/phrases (case-insensitive).
    
    :param input_csv: Path to the input CSV file
    :param output_csv: Path to save the filtered CSV file
    :param remove_list: List of words/phrases to filter out rows
    """
    # Load the CSV file
    df = pd.read_csv(input_csv)

    # Convert remove_list to lowercase for case-insensitive matching
    remove_list_lower = [item.lower() for item in remove_list]

    # Filter rows where 'Reference' does not match any of the words/phrases exactly (case-insensitive)
    filtered_df = df[~df['Reference'].str.lower().isin(remove_list_lower)]

    # Save the filtered DataFrame to a new CSV file
    filtered_df.to_csv(output_csv, index=False)
    print(f"Filtered CSV saved to {output_csv}")

# List of ambiguous words
remove_list = [
    # General Ambiguous Words
    "email", "emails", "attachment", "file", "document", "page", "link", "reference", 
    "item", "note", "copy", "section", "aconex", "attachments", "invoice", "embedded",
    "layout", "photo", "photos", "nrtjv", "attach",
    
    # # Filler Words
    # "here", "there", "this", "that",
    
    # # Placeholder Phrases
    # "see attached", "as per above", "refer to", "for more", "additional details",
    
    # Vague Temporal References
    "now", "later", "soon", "currently", "previously",
    
    # Action-Oriented Words
    "click", "open", "view", "check", "read",
    
    # Miscellaneous
    "report", "summary", "draft", "confidential", "attachment",
    
    # Common Patterns (can use regex for specific patterns instead of hardcoding)
    "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20",
    "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",  # Roman numerals
    "A1", "B2", "C3", "D4", "E5", "F6",  # Simple alphanumerics
    "XX", "TBD", "N/A"
]

# File variables
input_csv = input("Paste the annotation CSV filepath here: ").strip().strip('"')
output_name = os.path.splitext(os.path.basename(input_csv))[0]
output_csv = os.path.join(os.path.dirname(input_csv), f"{output_name}_Cleaned.csv")

# Run the function
remove_rows_by_reference(input_csv, output_csv, remove_list)
