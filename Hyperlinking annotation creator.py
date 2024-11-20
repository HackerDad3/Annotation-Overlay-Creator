import fitz  # PyMuPDF
import csv
import json
import re
from time import time
import os
from tqdm import tqdm  # Progress bar

# User email to show in notes
user_email = "trial.solutions@advancediscovery.io"

# File paths
input_file = r"C:\Users\Willi\Downloads\20241120T0522_UTC_Colin Fox docs_nan.csv"
pdf_directory = r"C:\Users\Willi\Downloads\OneDrive_1_18-11-2024\20241115_ClydeCo - Naude Production\Documents\AJD\001\001"

# Determine delimiter based on file extension
input_delimiter = '\t' if input_file.endswith('.txt') else ','

# Output CSV paths
output_csv = os.path.join(os.path.dirname(input_file), "annotation_output.csv")
phrases_output_csv = os.path.join(os.path.dirname(input_file), "phrases_output.csv")

# Initialize lists to store matched and unmatched phrases globally
matched_phrases = []
unmatched_phrases = []

# Create or overwrite the output CSV files
with open(output_csv, mode='w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['Bates/Control #', 'Annotation Data']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

with open(phrases_output_csv, mode='w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['Phrase', 'Matched']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

# Read the target phrases and their links from the input file
with open(input_file, newline='', encoding='utf-8') as file:
    reader = list(csv.DictReader(file, delimiter=input_delimiter))  # Convert to list for tqdm

    # Loop through all PDF files in the directory
    for pdf_file in tqdm([f for f in os.listdir(pdf_directory) if f.endswith('.pdf')], desc="Processing PDFs"):
        pdf_path = os.path.join(pdf_directory, pdf_file)
        pdf_filename_no_ext = os.path.splitext(pdf_file)[0]

        # Open the PDF file
        doc = fitz.open(pdf_path)

        # Create lists to store all annotation data for this PDF
        all_annotations = []
        pdf_matched_phrases = []
        pdf_unmatched_phrases = []

        for row in tqdm(reader, desc=f"Processing phrases in {pdf_file}", leave=False):
            phrase = row['Reference']
            link = row['Link']
            matched = False  # Flag to track if the phrase is matched

            # 1. **Search for Exact Matches**
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # Search for the exact phrase
                instances = page.search_for(phrase)
                
                if instances:
                    matched = True
                    pdf_matched_phrases.append(phrase)
                    for inst in instances:
                        rect = fitz.Rect(inst)
                        annotation_data = create_annotation_data(rect, page_num, phrase, link)
                        all_annotations.append(annotation_data)
                    break

            # 2. **Search for Flexible Matches**
            if not matched:
                flexible_pattern = re.escape(phrase).replace(r'\-', r'\-\s*').replace(r'\,', r'\,\s*')

                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    page_text = page.get_text("text")

                    for match in re.finditer(flexible_pattern, page_text, re.IGNORECASE):
                        matched = True
                        pdf_matched_phrases.append(phrase)
                        
                        start, end = match.span()
                        match_text = page_text[start:end]
                        lines = match_text.splitlines()

                        for line in lines:
                            quads = page.search_for(line)
                            for quad in quads:
                                rect = fitz.Rect(quad)
                                annotation_data = create_annotation_data(rect, page_num, phrase, link)
                                all_annotations.append(annotation_data)

                        break

            # If no matches were found, log it as unmatched
            if not matched:
                pdf_unmatched_phrases.append(phrase)

        # Combine all the annotations into the final JSON annotation group for this PDF
        if all_annotations:
            combined_annotations = "\\u0013".join(all_annotations)
            annotation_json = f"{{\"Highlights\":\"{combined_annotations}\"}}"

            # Append annotation data to the output CSV
            with open(output_csv, mode='a', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=['Bates/Control #', 'Annotation Data'])
                writer.writerow({'Bates/Control #': pdf_filename_no_ext, 'Annotation Data': annotation_json})

        # Append matched/unmatched phrases to the phrases output CSV
        with open(phrases_output_csv, mode='a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=['Phrase', 'Matched'])
            for phrase in pdf_matched_phrases:
                writer.writerow({'Phrase': phrase, 'Matched': 'Yes'})
            for phrase in pdf_unmatched_phrases:
                writer.writerow({'Phrase': phrase, 'Matched': 'No'})

        # Close the PDF document
        doc.close()

print(f"Processing complete. Results saved to:\n{output_csv}\n{phrases_output_csv}")
