import fitz  # PyMuPDF

INPUT_PATH = "/content/drive/MyDrive/input.pdf"
OUTPUT_PATH = "bold_lines.txt"


def is_span_bold(span):
    """
    Detect bold via font name or font flags.
    """
    font_name = span["font"].lower()
    flags = span["flags"]

    # Heuristic 1: font name contains "bold"
    if "bold" in font_name:
        return True

    # Heuristic 2: bold flag bit (usually bit 4 = 2^4 = 16)
    if flags & 16:
        return True

    return False


def line_is_entirely_bold(line):
    """
    A line is entirely bold if:
    - It has text
    - All non-whitespace spans are bold
    """
    spans = line["spans"]

    has_text = False

    for span in spans:
        text = span["text"].strip()
        if not text:
            continue

        has_text = True

        if not is_span_bold(span):
            return False

    return has_text


def extract_bold_lines():
    doc = fitz.open(INPUT_PATH)
    bold_lines = []

    for page in doc:
        blocks = page.get_text("dict")["blocks"]

        for block in blocks:
            if "lines" not in block:
                continue

            for line in block["lines"]:
                if line_is_entirely_bold(line):
                    full_text = "".join(span["text"] for span in line["spans"])
                    bold_lines.append(full_text.strip())

    doc.close()

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for line in bold_lines:
            f.write(line + "\n")

    print(f"Done. {len(bold_lines)} bold lines written to {OUTPUT_PATH}")


if __name__ == "__main__":
    extract_bold_lines()