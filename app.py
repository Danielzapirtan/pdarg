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

    for span in line["spans"]:
        text = span["text"].strip()
        if text:
            spans.append(span)

    if not spans:
        return False

    for span in spans:
        font_name = span["font"].lower()
        is_bold_flag = span["flags"] & 16  # bold flag in PyMuPDF
        return is_bold_flag

    return True


def extract_bold_lines(pdf_path):
    doc = fitz.open(pdf_path)
    bold_lines = []

    for page in doc:
        blocks = page.get_text("dict")["blocks"]

        for block in blocks:
            if block["type"] != 0:
                continue

            for line in block["lines"]:
                if line_is_fully_bold(line):
                    line_text = "".join(span["text"] for span in line["spans"]).strip()
                    if line_text:
                        bold_lines.append(line_text)

    doc.close()
    return bold_lines


def main():
    bold_lines = extract_bold_lines(INPUT_PATH)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for line in bold_lines:
            f.write(line + "\n")

    print(f"Extracted {len(bold_lines)} bold lines.")


if __name__ == "__main__":
    main()
