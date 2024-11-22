import os
from datetime import datetime, timedelta

# Function to process the filenames
def process_filenames(input_file):
    # Get the directory and filename of the input file
    input_dir = os.path.dirname(input_file)
    input_filename = os.path.basename(input_file)
    
    # Get the current UTC time and convert it to UTC+8
    utc_now = datetime.utcnow() + timedelta(hours=8)
    formatted_time = utc_now.strftime("%Y%m%dT%H%M")
    
    # Create the output file path with the formatted date-time and input file name
    output_file = os.path.join(input_dir, f"{formatted_time}_UTC8_{input_filename}.txt")
    
    # Read the input file
    with open(input_file, 'r') as infile:
        # Read all lines from the input file
        filenames = infile.readlines()

    # Remove the newline characters and file extensions
    filenames_no_extension = [os.path.splitext(filename.strip())[0] for filename in filenames]

    # Write the modified filenames to the output file
    with open(output_file, 'w') as outfile:
        for filename in filenames_no_extension:
            outfile.write(f"{filename}\n")

    print(f"Processed filenames have been written to {output_file}")

# Example usage
input_file = r"C:\Users\Willi\Downloads\Civmec Reports and Overlays\Civmec LAY.MUR.001 Hyperlinking\LAY.MUR.001 Filenames.txt"
process_filenames(input_file)
