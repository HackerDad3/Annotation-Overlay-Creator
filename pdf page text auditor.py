import fitz
import os
import datetime

def extract_page_text(pdf_path, page_number, output_path):
    # Open the PDF with fitz
    doc = fitz.open(pdf_path)
    
    # Convert page_number to int if it’s a string
    page_number = int(page_number)
    
    # Load the specified page (0-based indexing)
    page = doc.load_page(page_number - 1)
    
    # Extract text from the page
    text = page.get_text()

    # Write the extracted text to the file
    with open(output_path, 'w', encoding='utf-8') as outfile:
        outfile.write(text if text else "")

    doc.close()

if __name__ == "__main__":
    pdf_path = input("Paste PDF filepath: ").strip().strip('"')
    input_pdf = os.path.normpath(pdf_path)
    page_num = input("Enter page number: ").strip()

    # Extract base name without extension and the directory of the PDF
    base_name = os.path.splitext(os.path.basename(input_pdf))[0]
    pdf_dir = os.path.dirname(input_pdf)

    # Get current date in YYYYMMDD format
    date_str = datetime.datetime.now().strftime("%Y%m%d")

    # Construct the output filename and path
    output_filename = f"{date_str}_{base_name}_PageNum_{page_num}.txt"
    output_txt = os.path.join(pdf_dir, output_filename)

    extract_page_text(input_pdf, page_num, output_txt)
    print(f"Extracted text from page {page_num} of '{input_pdf}' into '{output_txt}'.")
