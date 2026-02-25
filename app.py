import os
import math
from collections import defaultdict, Counter
from pathlib import Path

import fitz  # PyMuPDF
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import ListFlowable, ListItem
from reportlab.lib import colors
from PyPDF2 import PdfReader, PdfWriter


INPUT_PDF = "/content/drive/MyDrive/input.pdf"
TEMP_TOC = "generated_toc.pdf"
OUTPUT_PDF = "output_with_contents.pdf"


# ------------------------------------------------------------
# STEP 1 — Extract font statistics and text blocks
# ------------------------------------------------------------

def extract_text_elements(pdf_path):
    doc = fitz.open(pdf_path)

    elements = []
    font_sizes = []

    for page_index, page in enumerate(doc):
        blocks = page.get_text("dict")["blocks"]

        for block in blocks:
            if block["type"] != 0:
                continue

            for line in block["lines"]:
                line_text = ""
                sizes = []

                for span in line["spans"]:
                    line_text += span["text"]
                    sizes.append(span["size"])

                clean = line_text.strip()
                if not clean:
                    continue

                avg_size = sum(sizes) / len(sizes)
                font_sizes.append(round(avg_size, 1))

                elements.append({
                    "text": clean,
                    "size": round(avg_size, 1),
                    "page": page_index + 1
                })

    doc.close()
    return elements, font_sizes


# ------------------------------------------------------------
# STEP 2 — Infer body font size and heading levels
# ------------------------------------------------------------

def determine_font_hierarchy(font_sizes):
    """
    Determine body size and heading levels automatically.
    """
    size_counts = Counter(font_sizes)

    # Body font = most frequent size
    body_size = size_counts.most_common(1)[0][0]

    # Heading sizes = larger than body
    heading_sizes = sorted(
        [size for size in size_counts if size > body_size],
        reverse=True
    )

    return body_size, heading_sizes


# ------------------------------------------------------------
# STEP 3 — Extract headings automatically
# ------------------------------------------------------------

def detect_headings(elements, body_size, heading_sizes):
    headings = []

    for el in elements:
        if el["size"] in heading_sizes:
            level = heading_sizes.index(el["size"]) + 1

            # Filter noise: avoid long paragraphs
            if len(el["text"]) < 200:
                headings.append({
                    "level": level,
                    "text": el["text"],
                    "page": el["page"]
                })

    return headings


# ------------------------------------------------------------
# STEP 4 — Build TOC PDF
# ------------------------------------------------------------

def build_toc_pdf(headings):
    doc = SimpleDocTemplate(TEMP_TOC)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("<b>Contents</b>", styles["Heading1"]))
    elements.append(Spacer(1, 0.4 * inch))

    max_level = max(h["level"] for h in headings) if headings else 1

    for h in headings:
        indent = 20 * (h["level"] - 1)

        style = ParagraphStyle(
            name=f"level_{h['level']}",
            parent=styles["Normal"],
            leftIndent=indent,
            spaceAfter=4
        )

        line = f"{h['text']}  ..........  {h['page']}"
        elements.append(Paragraph(line, style))

    doc.build(elements)


# ------------------------------------------------------------
# STEP 5 — Prepend TOC to original PDF
# ------------------------------------------------------------

def prepend_toc(original_pdf, toc_pdf, output_pdf):
    reader_original = PdfReader(original_pdf)
    reader_toc = PdfReader(toc_pdf)
    writer = PdfWriter()

    # Add TOC pages first
    for page in reader_toc.pages:
        writer.add_page(page)

    # Add original PDF pages
    for page in reader_original.pages:
        writer.add_page(page)

    with open(output_pdf, "wb") as f:
        writer.write(f)


# ------------------------------------------------------------
# MAIN EXECUTION
# ------------------------------------------------------------

def main():
    elements, font_sizes = extract_text_elements(INPUT_PDF)

    body_size, heading_sizes = determine_font_hierarchy(font_sizes)

    headings = detect_headings(elements, body_size, heading_sizes)

    build_toc_pdf(headings)

    prepend_toc(INPUT_PDF, TEMP_TOC, OUTPUT_PDF)

    print("Done.")
    print(f"Body font size detected: {body_size}")
    print(f"Heading levels detected: {heading_sizes}")
    print(f"Output file: {OUTPUT_PDF}")


if __name__ == "__main__":
    main()