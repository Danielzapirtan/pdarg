import fitz  # PyMuPDF
import os
import re

# Configuration
INPUT_PATH = "/content/drive/MyDrive/input.pdf"
OUTPUT_PATH = "/content/drive/MyDrive/output.txt"

def line_is_fully_bold(line):
    """
    Improved detection using flags, common bold suffixes, 
    and CSS-style weight numbers (e.g., W600, Black, etc.)
    """
    spans = [s for s in line.get("spans", []) if s.get("text", "").strip()]
    if not spans:
        return False

    # Expanded list: 'w6', 'w7', 'w8', 'w9' catch numerical weights like W600-W900
    bold_patterns = ["bold", "heavy", "black", "semibold", "demi", "medium", "w6", "w7", "w8", "w9"]

    for span in spans:
        font_name = span.get("font", "").lower()
        flags = span.get("flags", 0)
        
        # 1. Standard PDF Bold Flag (Bit 4)
        is_bold_flag = bool(flags & 16)
        
        # 2. Keyword/Weight Pattern check
        has_bold_name = any(word in font_name for word in bold_patterns)
        
        # 3. Specific check for fonts named like "Arial-BoldMT" or "Inter-SemiBold"
        # Often the hyphenated suffix is the only indicator
        if not (has_bold_name or is_bold_flag):
            return False

    return True

def extract_bold_lines_with_pages(pdf_path):
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
        page_num = page.number + 1
        
        for block in page_dict.get("blocks", []):
            if block.get("type") != 0:
                continue

            for line in block.get("lines", []):
                if line_is_fully_bold(line):
                    line_text = "".join(s.get("text", "") for s in line.get("spans", [])).strip()
                    if line_text:
                        results.append((page_num, line_text))
                
                # --- OPTIONAL DEBUGGING ---
                # Uncomment the lines below if it still finds nothing 
                # to see what your PDF fonts are actually named:
                # else:
                #    for s in line.get("spans", []):
                #        if s.get("text", "").strip():
                #            print(f"DEBUG: Text '{s['text'][:10]}' has font '{s['font']}'")

    doc.close()
    return results

def main():
    print(f"Analyzing PDF: {INPUT_PATH}...")
    bold_data = extract_bold_lines_with_pages(INPUT_PATH)
    
    if not bold_data:
        print("\n[!] No bold headings found.")
        print("Try uncommenting the DEBUG lines in extract_bold_lines_with_pages to see font names.")
        return

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(f"{'PAGE':<8} | {'HEADING'}\n")
        f.write("-" * 60 + "\n")
        for page_num, text in bold_data:
            f.write(f"Page {page_num:<3} | {text}\n")
    
    print(f"Success! {len(bold_data)} headings saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
