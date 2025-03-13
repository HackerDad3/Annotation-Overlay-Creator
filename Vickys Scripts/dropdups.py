import pandas as pd
import os

# Load the CSV file
input_csv = input("Paste filepath for input text file: ").strip().strip('"')
input_no_ext = os.path.splitext(os.path.basename(input_csv))[0]

df = pd.read_csv(input_csv, delimiter='\t')

# Print the column names to debug
print("Columns in DataFrame:", df.columns.tolist())

# Strip whitespace from column names
df.columns = df.columns.str.strip()

# Specify the columns to define uniqueness
columns_to_check = ['Reference', 'Link']  # Ensure these match the actual column names

# Check if the specified columns exist in the DataFrame
missing_columns = [col for col in columns_to_check if col not in df.columns]
if missing_columns:
    print("Missing columns:", missing_columns)
else:
    # Drop duplicates based on the specified columns
    unique_df = df.drop_duplicates(subset=columns_to_check)

    # Optionally, reset the index
    unique_df.reset_index(drop=True, inplace=True)

    # Save the result to a new CSV file
    output_csv = os.path.join(os.path.dirname(input_csv), f"{input_no_ext}Uniques.csv")
    unique_df.to_csv(output_csv, index=False)

    print("Unique rows saved to:", output_csv)