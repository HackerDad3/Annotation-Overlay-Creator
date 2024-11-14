import pandas as pd
import os
from datetime import datetime

# Define input Excel file path
input_file = r"C:\Users\Willi\Downloads\LAY.JOH.002 refrences.xlsx"

# Read the Excel file into a DataFrame and strip whitespace from column names
df = pd.read_excel(input_file)
df.columns = df.columns.str.strip()  # Remove leading/trailing spaces from column names

# Ensure required columns are present
required_columns = ['Report', 'Folder Reference', 'Aconex Reference', 'Link']
if not all(col in df.columns for col in required_columns):
    print(f"Columns found in the file: {df.columns.tolist()}")
    raise ValueError("The input Excel file must contain the columns: 'Report', 'Folder Reference', 'Aconex Reference', 'Link'")

# Extract the 'Report' value for suffixing the output file
report_value = df['Report'].iloc[0] if not df['Report'].empty else "UnknownReport"

# Step 1: Deduplicate rows based on Folder Reference, Aconex Reference, and Link
df = df.drop_duplicates(subset=['Folder Reference', 'Aconex Reference', 'Link'])

# Step 2: Group by 'Folder Reference' and concatenate unique 'Link' values
folder_group = df.groupby('Folder Reference', as_index=False).agg({
    'Link': lambda x: ''.join(pd.unique(x))
})
folder_group['Reference'] = folder_group['Folder Reference']
folder_group = folder_group[['Reference', 'Link']]

# Step 3: Group by 'Aconex Reference' and concatenate unique 'Link' values
aconex_group = df.groupby('Aconex Reference', as_index=False).agg({
    'Link': lambda x: ''.join(pd.unique(x))
})
aconex_group['Reference'] = aconex_group['Aconex Reference']
aconex_group = aconex_group[['Reference', 'Link']]

# Step 4: Combine both groups into a single DataFrame
combined_df = pd.concat([folder_group, aconex_group], ignore_index=True)

# Generate the output file name
current_time = datetime.utcnow().strftime('%Y%m%dT%H%M_UTC')
base_name = os.path.splitext(os.path.basename(input_file))[0]
output_filename = f"{current_time}_{base_name}_{report_value}.csv"
output_filepath = os.path.join(os.path.dirname(input_file), output_filename)

# Save the DataFrame to CSV
combined_df.to_csv(output_filepath, index=False, encoding='utf-8')

print(f"Done! Grouped and deduplicated data saved to: {output_filepath}")
