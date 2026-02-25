import fitz  # PyMuPDF

INPUT_PATH = "/content/drive/MyDrive/input.pdf"
OUTPUT_PATH = "/content/drive/MyDrive/output.txt"


def line_is_fully_bold(line):
    """
    A line is considered fully bold if:
    - It has text
    - Every text span in the line uses a bold font
    """
    spans = []

    # Fixed: line is a dictionary, need to access "spans" directly
    for span in line["spans"]:
        text = span.get("text", "").strip()  # Added .get() for safety
        if text:
            spans.append(span)

    if not spans:
        return False

    for span in spans:
        font_name = span.get("font", "").lower()  # Added .get() for safety
        # Fixed: Check if flags exists and is an integer
        flags = span.get("flags", 0)
        is_bold_flag = bool(flags & 18)  # bold flag in PyMuPDF
        
        if "bold" not in font_name and not is_bold_flag:
            return False

    return True


def extract_bold_lines(pdf_path):
    try:  # Added error handling
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"Error opening PDF: {e}")
        return []
    
    bold_lines = []

    for page in doc:
        page_dict = page.get_text("dict")
        blocks = page_dict.get("blocks", [])  # Added .get() for safety

        for block in blocks:
            if block.get("type") != 0:  # Added .get() for safety
                continue

            lines = block.get("lines", [])  # Added .get() for safety
            for line in lines:
                if line_is_fully_bold(line):
                    # Fixed: Build text from spans with safety checks
                    line_text_parts = []
                    for span in line.get("spans", []):
                        line_text_parts.append(span.get("text", ""))
                    line_text = "".join(line_text_parts).strip()
                    
                    if line_text:
                        bold_lines.append(line_text)

    doc.close()
    return bold_lines


def main():
    bold_lines = extract_bold_lines(INPUT_PATH)
    
    # Added directory creation if needed
    import os
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for line in bold_lines:
            f.write(line + "\n")

    print(f"Extracted {len(bold_lines)} bold lines.")


if __name__ == "__main__":
    main()