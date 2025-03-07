import fitz  # PyMuPDF
import pandas as pd
import re
import os
from tqdm import tqdm
import datetime

# --- Configuration ---
# Regex pattern to find desired strings (current document id numbering)
regex_pattern = (
    r'([A-Z]{3,5}\.\s*[A-Z0-9]{3,4}\.\s*[0-9]{3,4}\.\s*[0-9]{3,6}(_\d{4})?)|'
    r'(Exhibit\s+(PLE|CWS|CE|RE|CL|RL|TER|JER|CEX|REX|ORD|TRX)-[A-Z0-9]{3,4}(?:-[A-Z0-9]{2,4})?(_\d{4})?)|'
    r'((PLE|CWS|CE|RE|CL|RL|TER|JER|CEX|REX|ORD|TRX)-[A-Z0-9]{2,4}(?:-[A-Z0-9]{2,4})?(_\d{4})?)|'
    r'(REX-[A-Z0-9]{3,4}\.[A-Z0-9]{3,4}(_\d{4})?)|'
    r'(Exhibit\s+(REX-[A-Z0-9]{3,4}\.[A-Z0-9]{3,4}(_\d{4})?))|'
    r'((CC|RC|TC|JC)\.[A-Z0-9]{3,4}[A-Z]?\.[A-Z0-9]{3}(_\d{4})?)|'
    r'(Exhibit\s+(CC|RC|TC|JC)\.[A-Z0-9]{3,4}[A-Z]?\.[A-Z0-9]{3}(_\d{4})?)'
)

# Dimensions (in points) for the stamp area in the top-right corner
STAMP_WIDTH = 100  
STAMP_HEIGHT = 50

# --- User Inputs ---
pdf_directory = input("Enter directory containing PDF files: ").strip().strip('"')
pdf_directory = os.path.normpath(pdf_directory)

# Set output CSV file path to the parent directory of pdf_directory.
parent_dir = os.path.dirname(pdf_directory)

# Create a date prefix in YYYYMMDD format
date_prefix = datetime.datetime.now().strftime("%Y%m%d")
output_csv_file = os.path.join(parent_dir, f"{date_prefix}_Regex Results.csv")
output_csv_notes = os.path.join(parent_dir, f"{date_prefix}_Regex Results Notes.csv")

# --- Gather all PDF files recursively ---
pdf_files = []
for root, dirs, files in os.walk(pdf_directory):
    for file in files:
        if file.lower().endswith('.pdf'):
            pdf_files.append(os.path.join(root, file))

results = []

# --- Process each PDF file with an outer progress bar ---
for pdf_path in tqdm(pdf_files, desc="Processing PDFs", unit="pdf"):
    pdf_file = os.path.basename(pdf_path)
    doc = fitz.open(pdf_path)
    
    # Process each page in the current PDF file
    for page_num in tqdm(range(len(doc)), desc=f"Processing pages in {pdf_file}", unit="page", leave=False):
        page = doc.load_page(page_num)
        page_rect = page.rect
        
        # Define the stamp area (top-right corner)
        stamp_area = fitz.Rect(page_rect.x1 - STAMP_WIDTH, page_rect.y0, page_rect.x1, page_rect.y0 + STAMP_HEIGHT)
        
        # Get full page text
        page_text = page.get_text("text")
        
        # Find all regex matches in the page text
        for match in re.finditer(regex_pattern, page_text, re.IGNORECASE):
            # Remove any newline characters and extra whitespace from matched text
            found_text = re.sub(r'[\r\n]+', ' ', match.group(0)).strip()
            
            # Use search_for to get bounding boxes of found text
            for rect in page.search_for(found_text):
                rect = fitz.Rect(rect)
                # Calculate intersection with stamp area and skip if >50% overlaps
                intersection = rect & stamp_area
                if rect.get_area() > 0 and (intersection.get_area() / rect.get_area() > 0.5):
                    continue
                
                # Record the result; page is output as 1-based
                results.append({
                    "Document": pdf_file,
                    "Page": page_num + 1,
                    "Matched Text": found_text
                })
    doc.close()

# --- Write the individual results to CSV ---
df = pd.DataFrame(results)
df.to_csv(output_csv_file, index=False, encoding="utf-8")
print(f"Output CSV written to {output_csv_file}")

# --- Aggregate matched text for notes ---
# The new CSV will have two columns: "Bates/Control #" and "Notes Text".
# "Bates/Control #" is the matched text.
# "Notes Text" lists each occurrence (document without extension and page) where the match was found.
agg = {}
for row in results:
    matched_text = row["Matched Text"]
    # Remove extension from document name
    doc_name = os.path.splitext(row["Document"])[0]
    page = row["Page"]
    if matched_text not in agg:
        agg[matched_text] = []
    agg[matched_text].append((doc_name, page))

# Build the aggregated notes data.
notes_data = []
for matched_text, occurrences in agg.items():
    # Each occurrence is formatted as "document at page", with page as a 4-digit number.
    lines = [f"{doc} at {str(page).zfill(4)}" for doc, page in occurrences]
    notes_text = "Referenced In:\n\n" + "\n\n".join(lines)
    notes_data.append({
        "Bates/Control #": matched_text,
        "Notes Text": notes_text
    })

df_notes = pd.DataFrame(notes_data)
df_notes.to_csv(output_csv_notes, index=False, encoding="utf-8")
print(f"Notes CSV written to {output_csv_notes}")
