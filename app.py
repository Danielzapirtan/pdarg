import re
from collections import Counter
import fitz  # PyMuPDF
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from PyPDF2 import PdfReader, PdfWriter

INPUT_PDF = "/content/drive/MyDrive/input.pdf"
TEMP_TOC = "generated_toc.pdf"
OUTPUT_PDF = "/content/drive/MyDrive/output_with_contents.pdf"


# ------------------------------------------------------------
# STEP 1 — Extract clean text lines (robust merging)
# ------------------------------------------------------------

def extract_clean_lines(pdf_path):
    doc = fitz.open(pdf_path)

    elements = []
    font_sizes = []

    for page_index, page in enumerate(doc):
        page_width = page.rect.width
        blocks = page.get_text("dict")["blocks"]

        for block in blocks:
            if block["type"] != 0:
                continue

            for line in block["lines"]:

                line_text = ""
                sizes = []
                x_positions = []

                for span in line["spans"]:
                    line_text += span["text"]
                    sizes.append(span["size"])
                    x_positions.append(span["bbox"][0])

                clean = line_text.strip()

                if not clean:
                    continue

                # Ignore tiny fragments
                if len(clean) < 3:
                    continue

                # Ignore right margin artifacts (page numbers etc.)
                if min(x_positions) > page_width * 0.8:
                    continue

                avg_size = round(sum(sizes) / len(sizes), 1)
                font_sizes.append(avg_size)

                elements.append({
                    "text": clean,
                    "size": avg_size,
                    "page": page_index + 1
                })

    doc.close()
    return elements, font_sizes


# ------------------------------------------------------------
# STEP 2 — Detect body font & heading hierarchy
# ------------------------------------------------------------

def determine_font_hierarchy(font_sizes):
    counts = Counter(font_sizes)
    body_size = counts.most_common(1)[0][0]

    heading_sizes = sorted(
        [size for size in counts if size > body_size],
        reverse=True
    )

    return body_size, heading_sizes


# ------------------------------------------------------------
# STEP 3 — Detect Chapter 1 start page
# ------------------------------------------------------------

# ------------------------------------------------------------
# STEP 4 — Detect headings cleanly
# ------------------------------------------------------------

def detect_headings(elements, body_size, heading_sizes, start_page):
    headings = []

    for el in elements:
        if el["page"] < start_page:
            continue

        if el["size"] in heading_sizes:

            # Avoid long paragraph misclassification
            if len(el["text"]) > 200:
                continue

            level = heading_sizes.index(el["size"]) + 1

            headings.append({
                "level": level,
                "text": el["text"],
                "page": el["page"]
            })

    return headings


# ------------------------------------------------------------
# STEP 5 — Build TOC PDF
# ------------------------------------------------------------

def build_toc_pdf(headings):
    doc = SimpleDocTemplate(TEMP_TOC)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("<b>Contents</b>", styles["Heading1"]))
    elements.append(Spacer(1, 0.4 * inch))

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
# STEP 6 — Prepend TOC
# ------------------------------------------------------------

def prepend_toc(original_pdf, toc_pdf, output_pdf):
    reader_original = PdfReader(original_pdf)
    reader_toc = PdfReader(toc_pdf)
    writer = PdfWriter()

    for page in reader_toc.pages:
        writer.add_page(page)

    for page in reader_original.pages:
        writer.add_page(page)

    with open(output_pdf, "wb") as f:
        writer.write(f)


# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------

def main():
    elements, font_sizes = extract_clean_lines(INPUT_PDF)

    body_size, heading_sizes = determine_font_hierarchy(font_sizes)

    start_page = 22

    headings = detect_headings(
        elements,
        body_size,
        heading_sizes,
        start_page
    )

    build_toc_pdf(headings)

    prepend_toc(INPUT_PDF, TEMP_TOC, OUTPUT_PDF)

    print("Done.")
    print(f"Body font size: {body_size}")
    print(f"Heading levels: {heading_sizes}")
    print(f"Chapter 1 starts at page: {start_page}")
    print(f"Output file: {OUTPUT_PDF}")


if __name__ == "__main__":
    main()