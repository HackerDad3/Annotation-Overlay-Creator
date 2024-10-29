import csv
import os

# File paths
input_file = r"C:\Users\Willi\Downloads\Annotation Test\Annotation creation\Input file.txt"  # Tab-delimited input file
output_file = os.path.splitext(input_file)[0] + '.csv'  # Output file with .csv extension

# Read the tab-delimited file and write to CSV
with open(input_file, mode='r', newline='', encoding='utf-8') as infile, open(output_file, mode='w', newline='', encoding='utf-8') as outfile:
    reader = csv.reader(infile, delimiter='\t')
    writer = csv.writer(outfile, delimiter=',')
    
    # Write all rows from the tab-delimited file to the CSV file
    for row in reader:
        writer.writerow(row)

print(f"Conversion complete! CSV file saved as: {output_file}")
