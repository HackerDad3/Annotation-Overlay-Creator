import pandas as pd
import os
from tqdm import tqdm

# Input file paths
our_csv = r"C:\Users\Willi\Downloads\20241112T1208_UTC8_Lay_Notes_Full_ExtractedNotes.csv"
master_csv = r"C:\Users\Willi\Downloads\20241112T1230_UTC8_ECA_Full_filenames.csv"

# Create output file path automatically
base_name = os.path.splitext(os.path.basename(our_csv))[0]
output_filename = f"{base_name}_FilenameMismatch.csv"
output_file = os.path.join(os.path.dirname(our_csv), output_filename)

# Load both CSV files into Pandas DataFrames
print("Loading CSV files...")
our_df = pd.read_csv(our_csv, encoding='utf-8-sig')
master_df = pd.read_csv(master_csv, encoding='utf-8-sig')

# Merge our CSV with the master CSV based on the Bates/Control #
print("Merging data...")
merged_df = pd.merge(
    our_df,
    master_df,
    left_on='Document ID',
    right_on='Bates/Control #',
    suffixes=('', '_master'),
    how='left'
)

# Initialize an empty list to store rows with mismatched filenames
mismatch_rows = []

# Use tqdm to show progress while iterating through the merged DataFrame
print("Checking for filename mismatches...")
for _, row in tqdm(merged_df.iterrows(), total=merged_df.shape[0], desc="Processing", ncols=100):
    if row['Filename'] != row['Filename_master']:
        mismatch_rows.append({
            'Bates/Control #': row['Bates/Control #'],
            'Note Text': row['Note Text'],
            'Document ID': row['Document ID'],
            'Filename': row['Filename'],
            'Master Bates/Control #': row['Bates/Control #_master'],
            'Master Filename': row['Filename_master']
        })

# Convert the mismatched rows to a DataFrame
output_df = pd.DataFrame(mismatch_rows)

# Write the output DataFrame to a CSV file
print("Writing output to CSV...")
output_df.to_csv(output_file, index=False, encoding='utf-8')

print(f"I'M AWESOME! Mismatched filenames saved to: {output_file}")
