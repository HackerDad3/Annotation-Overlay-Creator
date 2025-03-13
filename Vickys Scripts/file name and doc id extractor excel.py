import pandas as pd
import os

# Load the Excel file (update with your actual file name)
input_file = input("Enter file path for Excel sheet: ").strip().strip('"')
output_path = os.path.dirname(input_file)
output_file = os.path.join(output_path,"Cleaned FileNames.xlsx")

# Read the Excel file
df = pd.read_excel(input_file)

# Remove file extensions
df["Reference"] = df["Original_Filename"].apply(lambda x: os.path.splitext(x)[0])

# Create new DataFrame with required columns
new_df = df[["Reference", "Document_ID"]].rename(columns={"Document_ID": "Link"})

# Save the new DataFrame to a new Excel file
new_df.to_excel(output_file, index=False)

print(f"🛠 File saved as {output_file}")
