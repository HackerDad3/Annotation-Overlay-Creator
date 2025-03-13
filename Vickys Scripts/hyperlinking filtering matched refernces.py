import fitz  # PyMuPDF
import csv
import os
import re
from tqdm import tqdm
from multiprocessing import Pool, cpu_count

# File paths
input_file = r"C:\Users\Vicky\Downloads\Noise References_AconexRefUniques.csv"
pdf_file = r"C:\Users\Vicky\Downloads\20250312_Noise\20250312_Noise\images\CEX-001_0001.pdf"

# Increase the CSV field size limit
csv.field_size_limit(10**7)

# Determine delimiter based on file extension
input_delimiter = '\t' if input_file.endswith('.txt') else ','

# Get the file name without extension for output
pdf_filename_no_ext = os.path.splitext(os.path.basename(pdf_file))[0]

def extract_pdf_text(pdf_path):
    """Extract all text from the PDF once (faster than searching page-by-page)."""
    doc = fitz.open(pdf_path)
    pdf_text = "\n".join([doc.load_page(i).get_text("text") for i in tqdm(range(len(doc)), desc="Extracting PDF Text")])
    doc.close()
    return pdf_text

def search_references(args):
    """Search for multiple references in the given PDF text."""
    refs, pdf_text = args  # Unpack arguments
    matched_refs = {}
    for phrase, link in refs:
        regex_pattern = re.escape(phrase)  # Escape special characters
        if re.search(regex_pattern, pdf_text, re.IGNORECASE):
            matched_refs[phrase] = link  # Store matches
    return matched_refs

if __name__ == "__main__":  # 🛠 Fix for Windows multiprocessing
    # Extract PDF text once
    pdf_text = extract_pdf_text(pdf_file)

    # Read references from CSV
    with open(input_file, newline='', encoding='utf-8-sig') as file:
        reader = list(csv.DictReader(file, delimiter=input_delimiter))
        references = [(row['Reference'], row['Link']) for row in reader]

    # **Use Multiprocessing to Speed Up Searching**
    num_workers = min(cpu_count(), 8)  # Use up to 8 cores
    chunk_size = max(1, len(references) // num_workers)  # Avoid zero-size chunks

    with Pool(num_workers) as pool:
        results = pool.map(search_references, [(references[i:i+chunk_size], pdf_text) for i in range(0, len(references), chunk_size)])

    # Combine results from all processes
    matched_phrases = {k: v for result in results for k, v in result.items()}

    # **Save Matched References to CSV**
    filtered_output_file = os.path.join(os.path.dirname(input_file), f"{pdf_filename_no_ext}_filtered.csv")
    with open(filtered_output_file, mode='w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Reference', 'Link']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for phrase, link in matched_phrases.items():
            writer.writerow({'Reference': phrase, 'Link': link})

    print(f"✅ Filtering Complete! Matched references saved to: {filtered_output_file}")