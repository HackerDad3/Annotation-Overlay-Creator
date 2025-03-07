import pandas as pd
import os

# Prompt for the input CSV file path
input_csv = input("Enter the path to the CSV file to clean: ").strip().strip('"')

# Read the CSV into a DataFrame
df = pd.read_csv(input_csv)

# Filter out rows where "Marked Text" is missing or empty (after stripping whitespace)
df_clean = df[df["Marked Text"].notna() & (df["Marked Text"].astype(str).str.strip() != '')]

# Create an output file path with a '_cleaned.csv' suffix
base_name = os.path.splitext(os.path.basename(input_csv))[0]
output_csv = os.path.join(os.path.dirname(input_csv), base_name + "_cleaned.csv")

# Save the cleaned DataFrame to the new CSV file
df_clean.to_csv(output_csv, index=False, encoding="utf-8")
print(f"Cleaned CSV saved to: {output_csv}")
