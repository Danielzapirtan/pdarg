import fitz  # PyMuPDF

def extract_large_text(input_path, output_path, min_font_size=7.9):
    """
    Extracts text spans from a PDF that exceed a specific font size.
    """
    extracted_lines = []

    try:
        # Open the PDF document
        doc = fitz.open(input_path)
        
        for page in doc:
            # "dict" gives us access to detailed attributes like font size
            page_dict = page.get_text("dict")
            blocks = page_dict.get("blocks", [])

            for b in blocks:
                if "lines" in b:
                    for l in b["lines"]:
                        for s in l["spans"]:
                            # Check if the font size exceeds our threshold
                            if s["size"] > min_font_size:
                                # Strip whitespace to keep the TXT clean
                                text = s["text"].strip()
                                if text:
                                    extracted_lines.append(text)
        
        doc.close()

        # Write the results to a text file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(extracted_lines))
            
        print(f"Success! Extracted {len(extracted_lines)} lines to {output_path}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Configuration
    INPUT_PDF = "/content/drive/MyDrive/input.pdf"
    OUTPUT_TXT = "/content/drive/MyDrive/extracted_text.txt"
    THRESHOLD = 7.5
    
    extract_large_text(INPUT_PDF, OUTPUT_TXT, THRESHOLD)
