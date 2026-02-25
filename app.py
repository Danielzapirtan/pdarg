# app.py
import json
import fitz  # pip install pymupdf
from pathlib import Path

BASE = Path("/content/drive/MyDrive")
INPUT_PDF   = BASE / "input.pdf"
TOC_JSON    = BASE / "toc.json"
OUTPUT_PDF  = BASE / "output.pdf"

def create_toc_doc(toc_data, page_width=595, page_height=842):
    """
    Creates a TOC document (can be multiple pages) with clickable links.
    toc_data: list of dicts like [{"title": "Chapter 1", "page": 3}, ...]
    'page' numbers refer to ORIGINAL document (1-based)
    """
    toc_doc = fitz.open()
    page = toc_doc.new_page(width=page_width, height=page_height)
    
    # Title
    page.insert_text(
        (72, 50),
        "Table of Contents",
        fontsize=20,
        fontname="helv",
        color=(0, 0, 0)
    )
    
    y = 90
    link_color = (0, 0, 1)  # blue
    
    for entry in toc_data:
        title = entry.get("title", "Untitled")
        orig_page_num = entry.get("page")  # 1-based, as in original PDF
        
        if not isinstance(orig_page_num, int) or orig_page_num < 1:
            orig_page_num = "?"
        
        # Display text: title + dots + page number
        display_text = f"{title} .................................... {orig_page_num}"
        
        # Insert visible text
        text_point = (72, y)
        page.insert_text(
            text_point,
            display_text,
            fontsize=12,
            fontname="helv",
            color=(0, 0, 0)
        )
        
        # Calculate clickable rectangle (around the whole line)
        # Rough estimate: text width ≈ len(display_text) * \~7 points at fontsize 12
        approx_width = len(display_text) * 6.5
        link_rect = fitz.Rect(
            72 - 4,          # slight left padding
            y - 14,          # above text baseline
            72 + approx_width + 4,
            y + 6            # below baseline
        )
        
        # Make it clickable → jump to top of target page
        # After we prepend TOC, original page N becomes page (N + toc_page_count)
        # But we use original page numbers here → final adjustment done later
        
        link_info = {
            "kind": fitz.LINK_GOTO,
            "page": orig_page_num - 1,   # 0-based for PyMuPDF
            "to": fitz.Point(72, 60),    # top-left-ish area of target page
            "from": link_rect,           # clickable area on THIS page
        }
        
        page.insert_link(link_info)
        
        y += 24  # line spacing
        
        # Simple page overflow handling
        if y > page_height - 80:
            page = toc_doc.new_page(width=page_width, height=page_height)
            y = 80
    
    return toc_doc


def main():
    if not INPUT_PDF.is_file():
        print(f"Error: {INPUT_PDF} not found")
        return
    
    if not TOC_JSON.is_file():
        print(f"Error: {TOC_JSON} not found")
        return
    
    # Read toc.json
    try:
        with open(TOC_JSON, encoding="utf-8") as f:
            toc = json.load(f)
    except Exception as e:
        print(f"Error reading {TOC_JSON}: {e}")
        return
    
    # Create TOC PDF with links (links point to original pages)
    toc_doc = create_toc_doc(toc)
    toc_page_count = len(toc_doc)
    
    # Open original document
    try:
        original = fitz.open(INPUT_PDF)
    except Exception as e:
        print(f"Error opening {INPUT_PDF}: {e}")
        return
    
    # Final document = TOC pages + original pages
    final = fitz.open()
    
    # Add TOC pages
    final.insert_pdf(toc_doc)
    
    # Add original pages
    final.insert_pdf(original)
    
    # Now fix the link targets: shift page numbers by toc_page_count
    # We loop through all pages that have our TOC links (the first toc_page_count pages)
    for pno in range(toc_page_count):
        page = final[pno]
        for link in page.links():  # generator over existing links
            if link["kind"] == fitz.LINK_GOTO:
                old_target = link["page"]  # 0-based, original
                new_target = old_target + toc_page_count
                link["page"] = new_target
                # Optional: you can also adjust "to" point if needed
                page.update_link(link)
    
    try:
        final.save(OUTPUT_PDF, garbage=3, deflate=True)
        print(f"Success! Created: {OUTPUT_PDF}")
        print(f"Total pages: {len(final)} (TOC {toc_page_count} + original {len(original)})")
        print("TOC entries are now clickable!")
    except Exception as e:
        print(f"Error saving {OUTPUT_PDF}: {e}")
    finally:
        final.close()
        original.close()
        toc_doc.close()


if __name__ == "__main__":
    main()