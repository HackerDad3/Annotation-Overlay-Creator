import pandas as pd
import os
import re

def remove_rows_by_reference(input_csv, output_csv, remove_list, regex_patterns=[]):
    """
    Remove rows from a CSV file where the 'Reference' column matches specific words/phrases (case-insensitive)
    or matches regex patterns.
    
    :param input_csv: Path to the input CSV file
    :param output_csv: Path to save the filtered CSV file
    :param remove_list: List of words/phrases to filter out rows
    :param regex_patterns: List of regex patterns to filter out rows
    """
    # Load the CSV file
    df = pd.read_csv(input_csv)

    # Convert remove_list to a set for efficient lookup and handle mixed types
    remove_list_lower = {str(item).lower() if isinstance(item, str) else item for item in remove_list}

    # Ensure the 'Reference' column is treated as a string for comparison, handling mixed types
    def match_reference(value):
        if pd.isna(value):
            return False  # Ignore NaN
        value_str = str(value).lower() if isinstance(value, str) else value

        # Check for exact matches in remove_list
        if value_str in remove_list_lower:
            return True

        # Check for regex pattern matches
        for pattern in regex_patterns:
            if re.fullmatch(pattern, str(value)):  # Use `fullmatch` to ensure the entire value matches the pattern
                return True

        return False

    # Apply filtering
    filtered_df = df[~df['Reference'].apply(match_reference)]

    # Save the filtered DataFrame to a new CSV file
    filtered_df.to_csv(output_csv, index=False)
    print(f"Filtered CSV saved to {output_csv}")

# List of ambiguous words and numbers
remove_list = [
    # General Ambiguous Words
    "email", "emails", "attachment", "file", "document", "page", "link", "reference", 
    "item", "note", "copy", "section", "aconex", "attachments", "invoice", "embedded",
    "layout", "photo", "photos", "nrtjv", "attach", "clash", "comments", "comment",
    "capture", "instruction", "position", "rates",
    
    # Vague Temporal References
    "now", "later", "soon", "currently", "previously",
    
    # Action-Oriented Words
    "click", "open", "view", "check", "read",
    
    # Miscellaneous
    "report", "summary", "draft", "confidential", "attachment",
    
    # Numbers and Roman Numerals
    1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
    "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",  # Roman numerals
    
    # Simple Alphanumerics
    "A1", "B2", "C3", "D4", "E5", "F6",
    "XX", "TBD", "N/A"
]

# Regex patterns to match numbers or specific patterns
regex_patterns = [
    r"\d{1,2}",         # Matches 1 or 2-digit numbers (e.g., 1, 23)
    # r"\d{3,4}",         # Matches 3 or 4-digit numbers (e.g., 123, 4567)
    # r"A\d{1}",          # Matches patterns like A1, A2
    # r"\d{1}-\d{2}",     # Matches patterns like 1-23, 5-99
    # r"XX",              # Matches exactly "XX"
]

# File variables
input_csv = input("Paste the annotation CSV filepath here: ").strip().strip('"')
output_name = os.path.splitext(os.path.basename(input_csv))[0]
output_csv = os.path.join(os.path.dirname(input_csv), f"{output_name}_Cleaned.csv")

# Run the function
remove_rows_by_reference(input_csv, output_csv, remove_list, regex_patterns)
