import fitz  # PyMuPDF

def extract_bold_lines(pdf_path):
    """
    Extracts lines containing bold text from a PDF.
    Format: <font_size> Bold Text Content
    """
    doc = fitz.open(pdf_path)
    extracted_data = []

    for page in doc:
        # Get structured text as a dictionary
        blocks = page.get_text("dict")["blocks"]
        
        for b in blocks:
            if b['type'] == 0:  # Block contains text
                for line in b["lines"]:
                    line_content = []
                    is_bold_line = False
                    max_font_size = 0
                    
                    for span in line["spans"]:
                        # Check font flags for 'bold'
                        # The 4th bit (binary 2^4 = 16) usually indicates bold
                        if span["flags"] & 2**4 or "bold" in span["font"].lower():
                            is_bold_line = True
                            line_content.append(span["text"])
                            # Track max font size in the line for the prefix
                            max_font_size = max(max_font_size, span["size"])
                    
                    if is_bold_line:
                        # Join spans and format with the angular bracket size
                        clean_text = "".join(line_content).strip()
                        if clean_text:
                            formatted_line = f"<{round(max_font_size, 2)}> {clean_text}"
                            extracted_data.append(formatted_line)
    
    doc.close()
    return extracted_data

# --- Usage Example ---
if __name__ == "__main__":
    pdf_file = "/content/drive/MyDrive/boox/dbt_bpd.pdf"  # Replace with your file path
    results = extract_bold_lines(pdf_file)
    
    for line in results:
        print(line)
