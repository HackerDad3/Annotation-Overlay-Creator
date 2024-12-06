import pandas as pd
import re
import os

def remove_last_underscore_suffix(name):
    """
    Removes the last underscore followed by 1–2 letters/numbers from the string.
    For example:
      - "filename_1" becomes "filename"
      - "myfile_ab" becomes "myfile"
      - "document_abc" remains "document_abc" since there are three characters after underscore
      - "report_9" becomes "report"
      - "report_99" becomes "report"
      - "data_!2" remains "data_!2" since '!' is not alphanumeric
    This should fix issues with _ within filenames
    """
    return re.sub(r'_[A-Za-z0-9]{1,2}$', '', name)

# Input file path
input_file = input("Enter the input Excel file path: ").strip().strip('"')

# Generate output file path
base_name, ext = os.path.splitext(input_file)
output_file = f"{base_name}_FilesRenamed{ext}"

# Column to process
column_name = input("Enter the column name to process: ").strip()

# Load the Excel file into a DataFrame
try:
    df = pd.read_excel(input_file)
except FileNotFoundError:
    print("The input file was not found. Please check the file path.")
    exit()
except OSError as e:
    print(f"Error reading the file: {e}")
    exit()

# Check if the specified column exists
if column_name not in df.columns:
    print(f"Column '{column_name}' not found in the Excel file.")
    exit()

# Process the specified column
df[column_name] = df[column_name].apply(lambda x: remove_last_underscore_suffix(x) if isinstance(x, str) else x)

# Save the updated DataFrame to a new Excel file
df.to_excel(output_file, index=False)
print(f"Updated file has been saved to {output_file}.")
