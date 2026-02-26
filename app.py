# app.py
# Requirements:
#   !apt update && apt install -y tesseract-ocr tesseract-ocr-eng poppler-utils
#   !pip install pytesseract pdf2image pillow

import os
from pathlib import Path
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import re

# ────────────────────────────────────────────────
# CONFIG
# ────────────────────────────────────────────────

BASE_DIR = Path("/content/drive/MyDrive")
INPUT_PDF  = BASE_DIR / "input.pdf"
OUTPUT_TXT = BASE_DIR / "toc.txt"

# Tesseract configuration
pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'
TESSDATA_PREFIX = '/usr/share/tesseract-ocr/5/tessdata'   # adjust if needed
os.environ['TESSDATA_PREFIX'] = TESSDATA_PREFIX

# Heuristics for detecting "bold" text
# (these values usually work quite well for academic papers / books)
SIZE_THRESHOLD = 13.0          # average font size considered "bold"
SIZE_VS_NORMAL_RATIO = 1.18    # how much larger than average line
CONFIDENCE_FLOOR = 60          # lower confidence → less reliable → penalize

# ────────────────────────────────────────────────

def is_likely_bold_word(word_info):
    """Simple but effective bold detection heuristic"""
    if not word_info:
        return False

    text = word_info['text'].strip()
    if not text:
        return False

    conf = float(word_info['conf'])
    size = float(word_info['size'])

    if conf < CONFIDENCE_FLOOR:
        return False

    # Very common academic bold patterns
    if re.match(r'^[A-Z0-9][A-Za-z0-9\s\.\-:–—()]{0,80}$', text):
        # All-caps or title-case short lines → very often headings
        if len(text.split()) <= 8 and size >= 11.5:
            return True

    # Main heuristic
    if size >= SIZE_THRESHOLD:
        return True

    return False


def is_likely_bold_line(line_dict):
    if not line_dict or 'words' not in line_dict or not line_dict['words']:
        return False

    words = line_dict['words']
    bold_words = [w for w in words if is_likely_bold_word(w)]

    if len(bold_words) == 0:
        return False

    # At least 60% of the words should look bold
    ratio = len(bold_words) / len(words)
    if ratio < 0.60:
        return False

    # Average size of bold words
    bold_sizes = [float(w['size']) for w in bold_words]
    avg_bold_size = sum(bold_sizes) / len(bold_sizes)

    if avg_bold_size < 12.0:
        return False

    return True


def main():
    if not INPUT_PDF.is_file():
        print(f"Error: File not found → {INPUT_PDF}")
        return

    print(f"Reading: {INPUT_PDF}")
    print("Converting PDF to images...")

    # Convert PDF → list of PIL images
    images = convert_from_path(INPUT_PDF, dpi=300, thread_count=2)

    bold_lines = []

    for i, img in enumerate(images, 1):
        print(f"  Processing page {i}/{len(images)} ...")

        # Get detailed OCR data with font size information
        data = pytesseract.image_to_data(
            img,
            lang='eng',
            output_type=pytesseract.Output.DICT,
            config='--psm 6'   # Assume uniform block of text
        )

        n = len(data['level'])

        current_line = []
        current_line_num = -1

        for j in range(n):
            level = data['level'][j]

            if level == 2:  # block
                continue
            if level == 3:  # paragraph
                continue
            if level == 4:  # line
                # New line → process previous one
                if current_line:
                    line_text = ' '.join(w['text'] for w in current_line if w['text'].strip())
                    line_text = re.sub(r'\s+', ' ', line_text).strip()

                    if line_text and is_likely_bold_line({'words': current_line}):
                        bold_lines.append(line_text)

                current_line = []
                current_line_num = data['line_num'][j]

            if level == 5:  # word
                if data['line_num'][j] != current_line_num:
                    # safety fallback
                    if current_line:
                        line_text = ' '.join(w['text'] for w in current_line if w['text'].strip())
                        line_text = re.sub(r'\s+', ' ', line_text).strip()
                        if line_text and is_likely_bold_line({'words': current_line}):
                            bold_lines.append(line_text)
                    current_line = []
                    current_line_num = data['line_num'][j]

                word_info = {
                    'text': data['text'][j],
                    'conf': data['conf'][j],
                    'size': data['height'][j] * 0.75,   # rough approximation px → pt
                }
                if word_info['text'].strip():
                    current_line.append(word_info)

        # Don't forget last line of page
        if current_line:
            line_text = ' '.join(w['text'] for w in current_line if w['text'].strip())
            line_text = re.sub(r'\s+', ' ', line_text).strip()
            if line_text and is_likely_bold_line({'words': current_line}):
                bold_lines.append(line_text)

    # ─── Save result ────────────────────────────────────────
    if bold_lines:
        with open(OUTPUT_TXT, 'w', encoding='utf-8') as f:
            for line in bold_lines:
                f.write(line + "\n")
        print(f"\nDone. Found {len(bold_lines)} likely bold lines.")
        print(f"Saved to: {OUTPUT_TXT}")
    else:
        print("\nNo bold lines were detected.")


if __name__ == "__main__":
    main()