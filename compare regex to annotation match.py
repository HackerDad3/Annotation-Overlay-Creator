import pandas as pd

def compare_csv_files(file1, file2):
    # Read the two CSV files
    df1 = pd.read_csv(file1, header=None)
    df2 = pd.read_csv(file2, header=None)
    
    # Extract the data from the first column as sets
    set1 = set(df1.iloc[:, 0].dropna().astype(str))
    set2 = set(df2.iloc[:, 0].dropna().astype(str))
    
    # Find common elements between the two sets
    common_elements = set1.intersection(set2)
    
    # Print the results
    if common_elements:
        print(f"Found {len(common_elements)} matching entries:")
        for match in common_elements:
            print(match)
    else:
        print("No matching entries found.")

# Usage
file1 = "file1.csv"  # Replace with the path to your first CSV file
file2 = "file2.csv"  # Replace with the path to your second CSV file
compare_csv_files(file1, file2)
