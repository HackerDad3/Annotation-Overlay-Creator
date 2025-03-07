import openpyxl
from tqdm import tqdm
import os

# Get file path from the user
file_path = input("Enter the full path to the Excel file: ").strip().strip('"')

# Load the workbook and select the active worksheet
workbook = openpyxl.load_workbook(file_path)
sheet = workbook.active

# Get the total number of rows
total_rows = sheet.max_row

# Add two rows beneath each existing row and adjust image anchors
with tqdm(total=total_rows, desc="Adding rows and adjusting images", unit="row") as pbar:
    for row in range(total_rows, 0, -1):  # Start from the last row and move upwards
        # Insert two rows below the current row
        sheet.insert_rows(row + 1, 2)

        # Adjust any images anchored to rows at or after this one
        if hasattr(sheet, '_images'):  # Check if there are images in the sheet
            for image in sheet._images:
                if hasattr(image.anchor, '_from') and hasattr(image.anchor, '_to'):
                    # Adjust starting row
                    if image.anchor._from.row >= row:
                        image.anchor._from.row += 2
                    # Adjust ending row
                    if image.anchor._to.row >= row:
                        image.anchor._to.row += 2

        pbar.update(1)

# Save the modified workbook in the same directory as the input file
output_path = os.path.join(os.path.dirname(file_path), "updated_" + os.path.basename(file_path))
workbook.save(output_path)
print(f"Updated file saved as {output_path}")
