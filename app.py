import fitz  # PyMuPDF
import os

# Configuration
INPUT_PATH = "/content/drive/MyDrive/input.pdf"
OUTPUT_PATH = "/content/drive/MyDrive/output.txt"

def line_is_fully_bold(line):
    """
    A line is considered fully bold if every non-whitespace span 
    matches bold, heavy, black, semibold, or demi keywords/flags.
    """
    # 1. Extract only spans that contain actual text (ignoring whitespace)
    spans = [s for s in line.get("spans", []) if s.get("text", "").strip()]

    if not spans:
        return False

    # 2. Strong weight keywords used in professional typography
    bold_keywords = ["bold", "heavy", "black", "semibold", "demi", "medium"]

    for span in spans:
        font_name = span.get("font", "").lower()
        flags = span.get("flags", 0)
        
        # PyMuPDF Bold Flag is bit 4 (value 16)
        is_bold_flag = bool(flags & 16)
        
        # Check if any keyword exists in the font name string
        has_bold_name = any(word in font_name for word in bold_keywords)
        
        # If the span isn't bold by name OR by flag, the whole line fails
        if not (has_bold_name or is_bold_flag):
            return False

    return True

def extract_bold_lines_with_pages(pdf_path):
    """
    Iterates through the PDF and returns a list of (page_num, text) tuples.
    """
    if not os.path.exists(pdf_path):
        print(f"Error: File not found at {pdf_path}")
        return []

    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"Error opening PDF: {e}")
        return []

    results = []

    for page in doc:
        page_dict = page.get_text("dict")
        page_num = page.number + 1  # 1-indexed for readability
        
        for block in page_dict.get("blocks", []):
            if block.get("type") != 0:  # Only process text blocks
                continue

            for line in block.get("lines", []):
                if line_is_fully_bold(line):
                    # Reconstruct the full text of the line
                    line_text = "".join(s.get("text", "") for s in line.get("spans", [])).strip()
                    if line_text:
                        results.append((page_num, line_text))

    doc.close()
    return results

def main():
    print(f"Starting extraction from: {INPUT_PATH}")
    bold_data = extract_bold_lines_with_pages(INPUT_PATH)
    
    if not bold_data:
        print("No bold headings detected. Check your PDF formatting or file path.")
        return

    # Ensure output directory exists
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    try:
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            f.write(f"{'PAGE':<8} | {'HEADING'}\n")
            f.write("-" * 50 + "\n")
            for page_num, text in bold_data:
                # Format as a clean Table of Contents
                f.write(f"Page {page_num:<3} | {text}\n")
        
        print(f"Success! Extracted {len(bold_data)} headings to {OUTPUT_PATH}")
    except Exception as e:
        print(f"Error writing to file: {e}")

if __name__ == "__main__":
    main()
