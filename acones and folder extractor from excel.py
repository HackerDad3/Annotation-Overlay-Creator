import pandas as pd
import os
from datetime import datetime
import pytz  # Import pytz for timezone conversion

# Define input Excel file path
# input_file = r"C:\Users\Willi\Downloads\Civmec Reports and Overlays\Civmec LAY.MCC.004 Hyperlinking\LAY.MCC.004 Aconex References.xlsx"
input_file = input("Paste the filepath for the Excel file with link refrences: ").strip().strip('"')

#normalize path
input_file = os.path.normpath(input_file)

# Read the Excel file into a DataFrame and strip whitespace from column names
df = pd.read_excel(input_file)
df.columns = df.columns.str.strip()  # Remove leading/trailing spaces from column names

# Ensure required columns are present
required_columns = ['Report', 'Folder Reference', 'Aconex Reference', 'Link']
if not all(col in df.columns for col in required_columns):
    print(f"Columns found in the file: {df.columns.tolist()}")
    raise ValueError("The input Excel file must contain the columns: 'Report', 'Folder Reference', 'Aconex Reference', 'Link'")

# Step 1: Remove file extensions from 'Aconex Reference' column
# Ensure all values in 'Aconex Reference' are treated as strings and extensions are removed
# df['Aconex Reference'] = df['Aconex Reference'].apply(lambda x: os.path.splitext(str(x))[0])

# Extract the 'Report' value for suffixing the output file
report_value = df['Report'].iloc[0] if not df['Report'].empty else "UnknownReport"

# Step 2: Deduplicate rows based on Folder Reference, Aconex Reference, and Link
df = df.drop_duplicates(subset=['Folder Reference', 'Aconex Reference', 'Link'])

# Step 3: Group by 'Folder Reference' and concatenate unique 'Link' values
folder_group = df.groupby('Folder Reference', as_index=False).agg({
    'Link': lambda x: ''.join(pd.unique(x))
})
folder_group['Reference'] = folder_group['Folder Reference']
folder_group = folder_group[['Reference', 'Link']]

# Step 4: Group by 'Aconex Reference' and concatenate unique 'Link' values
aconex_group = df.groupby('Aconex Reference', as_index=False).agg({
    'Link': lambda x: ''.join(pd.unique(x))
})
aconex_group['Reference'] = aconex_group['Aconex Reference']
aconex_group = aconex_group[['Reference', 'Link']]

# Step 5: Combine both groups into a single DataFrame
combined_df = pd.concat([folder_group, aconex_group], ignore_index=True)

# Generate the output file name with 'Australia/Perth' time zone
utc_now = datetime.utcnow().replace(tzinfo=pytz.utc)  # Get the current UTC time
perth_tz = pytz.timezone('Australia/Perth')  # Define 'Australia/Perth' timezone
current_time = utc_now.astimezone(perth_tz).strftime('%Y%m%d')

# Remove the extension from the input file name
base_name = os.path.splitext(os.path.basename(input_file))[0]

# Construct output filename based on report value and base name
output_filename = f"{current_time}_{base_name}_{report_value}.csv"
output_filepath = os.path.join(os.path.dirname(input_file), output_filename)

# Save the DataFrame to CSV
combined_df.to_csv(output_filepath, index=False, encoding='utf-8')

print(f"Done! Go Me!! Grouped and deduplicated data saved to: {output_filepath}")
