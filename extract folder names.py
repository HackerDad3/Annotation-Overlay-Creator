import os

def extract_directory_by_level(input_file, folder_level):
    """
    Reads file paths from the input file, extracts the specified directory name
    by level, and writes the results to a new file with `_FolderNames` added to the input filename.
    
    Args:
        input_file (str): Path to the input text file containing file paths.
        folder_level (int): Level of the folder to extract.
            Positive values count from the root (1-based index).
            Negative values count from the end (-1 for last, -2 for second-to-last, etc.).
    """
    # Generate output file path
    base_name, ext = os.path.splitext(input_file)
    output_file = f"{base_name}_FolderNames{ext}"

    with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
        for line in infile:
            # Strip whitespace and split the file path
            filepath = line.strip()
            if not filepath:
                continue  # Skip empty lines
            
            # Split the path into parts
            parts = filepath.split('/')
            
            try:
                # Extract the specified directory by level
                directory_name = parts[folder_level]
                outfile.write(directory_name + '\n')
            except IndexError:
                # If the specified folder level doesn't exist, write an error message or leave blank
                outfile.write('Invalid level\n')
    
    print(f"Directory names have been written to {output_file}.")

# Input file path
input_file_path = input("Enter the input file path: ").strip().strip('"')

# Ask the user for the folder level to extract
folder_level = int(input("Enter the folder level to extract (e.g., -2 for second-to-last): ").strip())

# Process the file
extract_directory_by_level(input_file_path, folder_level)
