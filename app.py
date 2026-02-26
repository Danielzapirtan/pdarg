# app.py

import os
from pathlib import Path
from pdf2image import convert_from_path, pdfinfo_from_path
import pytesseract
import re

# ────────────────────────────────────────────────
# CONFIG
# ────────────────────────────────────────────────

BASE_DIR = Path(os.getenv("BASE_DIR", "."))
INPUT_PDF = BASE_DIR / os.getenv("INPUT_PDF", "input.pdf")
OUTPUT_TXT = BASE_DIR / os.getenv("OUTPUT_TXT", "toc.txt")

pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"
os.environ["TESSDATA_PREFIX"] = "/usr/share/tesseract-ocr/5/tessdata"

DPI = 230
CONFIDENCE_FLOOR = 60
SIZE_THRESHOLD = 13.0

# ────────────────────────────────────────────────

def is_likely_bold_word(word_info):
    text = word_info["text"].strip()
    if not text:
        return False

    if float(word_info["conf"]) < CONFIDENCE_FLOOR:
        return False

    if float(word_info["size"]) >= SIZE_THRESHOLD:
        return True

    if re.match(r'^[A-Z0-9][A-Za-z0-9\s\.\-:–—()]{0,80}$', text):
        return True

    return False


def is_likely_bold_line(words):
    if not words:
        return False

    bold = [w for w in words if is_likely_bold_word(w)]
    if not bold:
        return False

    if len(bold) / len(words) < 0.6:
        return False

    avg_size = sum(float(w["size"]) for w in bold) / len(bold)
    return avg_size >= 12.0


def process_page(img):
    data = pytesseract.image_to_data(
        img,
        lang="eng",
        output_type=pytesseract.Output.DICT,
        config="--psm 6 -c preserve_interword_spaces=1"
    )

    results = []
    current_words = []
    prev_line = -1

    for i in range(len(data["level"])):
        if data["level"][i] != 5:
            continue
        if not data["text"][i].strip():
            continue

        line = data["line_num"][i]

        if line != prev_line and current_words:
            line_text = " ".join(w["text"] for w in current_words)
            line_text = re.sub(r"\s+", " ", line_text).strip()

            if is_likely_bold_line(current_words):
                results.append(line_text)

            current_words = []

        word = {
            "text": data["text"][i],
            "conf": data["conf"][i],
            "size": float(data["height"][i]) * 0.72,
        }

        current_words.append(word)
        prev_line = line

    if current_words:
        line_text = " ".join(w["text"] for w in current_words)
        line_text = re.sub(r"\s+", " ", line_text).strip()
        if is_likely_bold_line(current_words):
            results.append(line_text)

    return results


def main():
    if not INPUT_PDF.exists():
        print("Input PDF not found.")
        return

    info = pdfinfo_from_path(INPUT_PDF)
    total_pages = info["Pages"]
    print(f"Total pages: {total_pages}")

    all_bold = []

    for page in range(1, total_pages + 1):
        print(f"Processing page {page}/{total_pages}")

        images = convert_from_path(
            INPUT_PDF,
            dpi=DPI,
            first_page=page,
            last_page=page
        )

        bold_lines = process_page(images[0])
        all_bold.extend(bold_lines)

    with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
        for line in all_bold:
            f.write(line + "\n")

    print(f"Done. Found {len(all_bold)} headings.")


if __name__ == "__main__":
    main()