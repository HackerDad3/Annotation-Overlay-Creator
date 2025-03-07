import re
import openpyxl

# Adjust this regex to fit your exact matching requirements.
# Explanation:
#  - Civmec-[\w-]+  -> Matches "Civmec-" followed by letters/digits/underscore/hyphen
#  - NRT IJV-[\w-]+ -> Matches "NRT IJV-" with a space, then letters/digits/underscore/hyphen
#  - NRTIJV-[\w-]+  -> Matches "NRTIJV-" (no space), then letters/digits/underscore/hyphen
#  - SE\d+[\w-]+    -> Matches "SE" followed by one or more digits, then letters/digits/underscore/hyphen
pattern = re.compile(
    r"(?:Civmec-[\w-]+|NRT IJV-[\w-]+|NRTIJV-[\w-]+|SE\d+[\w-]+)",
    re.IGNORECASE
)

def extract_matches_from_excel(input_file, output_file):
    # Load the workbook and select the active worksheet
    wb = openpyxl.load_workbook(input_file, data_only=True)
    ws = wb.active

    # Use a set to avoid duplicates
    all_matches = set()

    # Iterate through rows and cells
    for row in ws.iter_rows(values_only=True):
        for cell_value in row:
            if isinstance(cell_value, str):
                # Find all occurrences that match our pattern in this cell
                found = pattern.findall(cell_value)
                for match in found:
                    all_matches.add(match)

    # Write the unique matches to a text file
    with open(output_file, "w", encoding="utf-8") as f:
        for match in sorted(all_matches):
            f.write(match + "\n")


if __name__ == "__main__":
    # Example usage:
    excel_file = "input.xlsx"    # Change to the path of your source Excel
    output_txt = "output.txt"    # Output file for extracted matches

    extract_matches_from_excel(excel_file, output_txt)
    print(f"Matches have been extracted to {output_txt}")
