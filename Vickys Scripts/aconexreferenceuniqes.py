import pandas as pd
import os

# Load data from Excel file
input_file = input("paste file path: ").strip().strip('"')
input_no_ext = os.path.splitext(os.path.basename(input_file))[0]
sheet_name = "Sheet1"  # Adjust to the sheet name in your Excel file
df = pd.read_excel(input_file, sheet_name=sheet_name)

# Rename columns to ensure consistency (adjust based on actual column names)
df.columns = ['Reference', 'Link']

# Drop duplicate references, keeping only the first occurrence
unique_df = df.drop_duplicates(subset=['Reference'])

# Group by 'Reference' and concatenate 'Link'
grouped = unique_df.groupby('Reference', as_index=False).agg({'Link': lambda x: ', '.join(x.dropna().astype(str))})

# Write the output to a tab-separated text file
output_file = os.path.join(os.path.dirname(input_file), f"{input_no_ext}_AconexRef.txt")
grouped.to_csv(output_file, sep='\t', index=False)

print(f"Data written to {output_file}")