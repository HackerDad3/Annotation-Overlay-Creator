import re
import csv
import os

def extract_words(input_file, output_file):
    # patterns I think I saw
    pattern = r'''
        \b                          # Word boundary
        (?:                        # Non capturing group for different patterns
            [A-Z]{3}-[A-Z]{3}-\d{4}-\d{7} |      # Matches NRT-CIV-1716-4577446
            Civmec-(?:[A-Z]{4,5}-\d{6}|[A-Z]{4}\d{6}) |               # Matches Civmec-XXXX-009918
            FE\d{3}-[A-Z]{3}-[A-Z]{3}-\d{3} (?:_\d+)? |    # Matches FE118-CLA-EOT-072
            #Civmec-[A-Z]{4}\d{6} |                  # Matches Civmec-XXXX008340.  ADDED TO PREVIOUS ONE WITH NON GROUPING
            NRT\s(?:IJV[A-Z]{3,6}|IJV-[A-Z]{3,6}|IJV[A-Z]{3,6}-|IJV-[A-Z]{3,6}-)(?:\d{6}|[A-Z]{4}\d{6}) |  # SHOULD BE UNIVERSAL FOR NRT IJV DOCS
            NRT (?:IJVWTRAN|IJV-WTRAN)-(?:\d{6}|[A-Z]{4}\d{6}) |        # Additions from Ben. updated to allow for missing 4 letters
            Civmec-TRANSMIT(?:\d{6}|[A-Z]{4}\d{6}) |  # Additions from Ben. updated
            NRT (?:IJVRTRFI|IJV-RTRFI)-(?:\d{6}|[A-Z]{4}\d{6}) |   # Additions from Ben. updated
            Civmec-RFI-(?:\d{6}|[A-Z]{4}\d{6}) |  # Additions from Ben
            NRT IJVGCOR-(?:\d{6}|[A-Z]{4}\d{6}) | # Additions from Ben
            CivmecGCOR-(?:\d{6}|[A-Z]{4}\d{6}) | # Additions from Ben
            CivmecGCOR(?:\d{6}|[A-Z]{4}\d{6}) | # Additions from Ben
            Civmec-RFI(?:\d{6}|[A-Z]{4}\d{6}) | # Additions from Ben
            IJV-RTRFI(?:\d{6}|[A-Z]{4}\d{6}) | # Additions from Ben
            DJV-ACTION(?:\d{6}|[A-Z]{4}\d{6}) | # Additions from Ben
            NWRLOTS-[A-Z]{2,3}-[A-Z]{2,3}-[A-Z]{2,3}-(?:[A-Z]{2,3}-|[A-Z]{2,3})\d{6}
        )
        \b                          # Word boundary
    '''

    # Initialize a list to hold the extracted words
    extracted_words = []

    # Read the input file
    with open(input_file, 'r', encoding='utf-8') as file:
        for line in file:
            # Find all matches in the line
            matches = re.findall(pattern, line, re.VERBOSE)  # Used verbose so it was easier to read and add more regex
            extracted_words.extend(matches)

    # Deduplicate the extracted words by converting the list to a set
    deduplicated_words = set(extracted_words)

    # Write the deduplicated words to a CSV file
    with open(output_file, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(['Extracted Text'])  # Adding the header
        for word in sorted(deduplicated_words):  # Optional: Sort for consistency
            csv_writer.writerow([word])

# Let er rip
input_file = r"C:\Users\Willi\Downloads\Annotation Test\Annotation creation\LayJoh005 Text.txt"
output_file = os.path.join(os.path.dirname(input_file), f'{os.path.splitext(os.path.basename(input_file))[0]}_ExtractedText.csv')
extract_words(input_file, output_file)
