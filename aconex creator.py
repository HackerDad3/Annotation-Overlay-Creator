import pandas as pd
import os

# Load data from Excel file
input_file = r"C:\Users\Willi\Downloads\LAY.JOH.025.xlsx" # Replace with your Excel file name
input_no_ext = os.path.splitext(os.path.basename(input_file))[0]

# Load Aconex Reference sheet
aconex_df = pd.read_excel(input_file, sheet_name="Aconex Reference")
aconex_df.columns = ['Reference', 'Link']
aconex_unique_df = aconex_df[['Reference', 'Link']].drop_duplicates()
aconex_grouped = aconex_unique_df.groupby('Reference')['Link'].apply(lambda x: ''.join(x)).reset_index()
aconex_output_file = os.path.join(os.path.dirname(input_file), f"{input_no_ext}AconexRef.txt")
aconex_grouped.to_csv(aconex_output_file, sep='\t', index=False)
print(f"Aconex data written to {aconex_output_file}")

# Load Folder Reference sheet
folder_df = pd.read_excel(input_file, sheet_name="Folder Reference")
folder_df.columns = ['Reference', 'Link']
folder_unique_df = folder_df[['Reference', 'Link']].drop_duplicates()
folder_grouped = folder_unique_df.groupby('Reference')['Link'].apply(lambda x: ''.join(x)).reset_index()
folder_output_file = os.path.join(os.path.dirname(input_file), f"{input_no_ext}FolderRef.txt")
folder_grouped.to_csv(folder_output_file, sep='\t', index=False)
print(f"Folder data written to {folder_output_file}")
