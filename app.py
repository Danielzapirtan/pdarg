# app.py
import fitz           # pip install PyMuPDF
import json
from pathlib import Path

BASE_DIR = Path("/content/drive/MyDrive")
INPUT_PDF = BASE_DIR / "input.pdf"
OUTPUT_JSON = BASE_DIR / "toc.json"

MIN_FONT_SIZE = 8.4

def main():
    if not INPUT_PDF.is_file():
        print(f"Error: File not found → {INPUT_PDF}")
        return

    doc = fitz.open(INPUT_PDF)
    toc_entries = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        blocks = page.get_text("dict")["blocks"]

        for block in blocks:
            if "lines" not in block:
                continue

            for line in block["lines"]:
                for span in line["spans"]:
                    text = span["text"].strip()
                    if not text:
                        continue

                    size = span["size"]
                    if size < MIN_FONT_SIZE:
                        continue

                    # Special rule: on the very first text line of a page → accept only if it's a pure number
                    is_first_line_of_page = (
                        block == blocks[0] and
                        line == block["lines"][0] and
                        span == line["spans"][0]
                    )

                    if is_first_line_of_page:
                        if not text.strip().isdigit():
                            continue  # skip unless it's 1, 42, 105 etc.

                    # If we reached here → we want this line
                    entry = {
                        "page": page_num + 1,
                        "text": text,
                        "font_size": round(size, 2),
                        "first_on_page": is_first_line_of_page
                    }
                    toc_entries.append(entry)

    doc.close()

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(toc_entries, f, ensure_ascii=False, indent=2)

    print(f"Done. Found {len(toc_entries)} entries.")
    print(f"Wrote → {OUTPUT_JSON}")

if __name__ == "__main__":
    main()