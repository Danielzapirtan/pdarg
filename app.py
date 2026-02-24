import fitz  # PyMuPDF
import re
from collections import defaultdict

# Hardcoded path to your PDF
PDF_PATH = "/content/drive/MyDrive/input.pdf"
OUTPUT_PATH = "table_of_contents.txt"

def get_baseline_font_size(doc):
    """Determine the most common font size for regular text"""
    font_sizes = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        blocks = page.get_text("dict")["blocks"]
        
        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        # Only consider non-bold text for baseline
                        if "bold" not in span["font"].lower():
                            font_sizes.append(span["size"])
    
    if font_sizes:
        # Return the most common size
        return max(set(font_sizes), key=font_sizes.count)
    return 10.0

def extract_headings(doc, baseline_size):
    """Extract all bold text with size > baseline"""
    headings = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        blocks = page.get_text("dict")["blocks"]
        
        for block in blocks:
            if "lines" not in block:
                continue
                
            for line in block["lines"]:
                line_text = ""
                line_size = 0
                line_font = ""
                spans_info = []
                
                # Collect all spans in this line
                for span in line["spans"]:
                    text = span["text"].strip()
                    if not text:
                        continue
                        
                    font = span["font"].lower()
                    size = span["size"]
                    
                    spans_info.append({
                        'text': text,
                        'font': font,
                        'size': size,
                        'bold': 'bold' in font or 'black' in font or 'heavy' in font
                    })
                
                # Check if this line might be a heading
                # A heading line should have consistent formatting
                if spans_info:
                    first_span = spans_info[0]
                    all_same_bold = all(s['bold'] == first_span['bold'] for s in spans_info)
                    all_same_size = all(abs(s['size'] - first_span['size']) < 0.5 for s in spans_info)
                    
                    if all_same_bold and all_same_size:
                        is_bold_line = first_span['bold']
                        line_size = first_span['size']
                        
                        # Check if it's bold AND larger than baseline
                        if is_bold_line and line_size > baseline_size * 1.05:  # 5% threshold
                            # Reconstruct the full line text
                            full_text = " ".join([s['text'] for s in spans_info])
                            
                            # Clean up the text
                            full_text = re.sub(r'\s+', ' ', full_text).strip()
                            
                            # Skip very short lines (likely not headings)
                            if len(full_text) < 3:
                                continue
                            
                            headings.append({
                                'text': full_text,
                                'size': line_size,
                                'page': page_num + 1,
                                'y0': line["bbox"][1]  # Top position
                            })
    
    return headings

def group_by_hierarchy(headings):
    """Group headings into hierarchical levels based on font size"""
    if not headings:
        return []
    
    # Sort headings by page and position
    headings.sort(key=lambda x: (x['page'], x['y0']))
    
    # Group by font size
    size_groups = defaultdict(list)
    for h in headings:
        size_groups[h['size']].append(h)
    
    # Sort sizes descending and assign levels
    unique_sizes = sorted(size_groups.keys(), reverse=True)
    size_to_level = {size: i+1 for i, size in enumerate(unique_sizes)}
    
    # Build hierarchical list
    result = []
    for heading in headings:
        result.append({
            'text': heading['text'],
            'level': size_to_level[heading['size']],
            'page': heading['page'],
            'indent': '   ' * (size_to_level[heading['size']] - 1)
        })
    
    return result

def save_toc(headings, output_path):
    """Save hierarchical TOC to text file"""
    with open(output_path, 'w', encoding='utf-8') as f:
        for heading in headings:
            text = heading['text']
            indent = heading['indent']
            page = heading['page']
            
            # Calculate dots for alignment (target 70 chars total)
            dots_count = max(1, 65 - len(indent) - len(text) - len(str(page)))
            dots = '.' * dots_count
            
            line = f"{indent}{text} {dots} {page}\n"
            f.write(line)
    
    print(f"TOC saved to {output_path}")

def main():
    print(f"Processing PDF: {PDF_PATH}")
    
    try:
        doc = fitz.open(PDF_PATH)
        print(f"PDF opened successfully. Pages: {len(doc)}")
        
        print("Analyzing document...")
        baseline_size = get_baseline_font_size(doc)
        print(f"Baseline font size: {baseline_size:.1f}")
        
        print("Extracting headings...")
        headings = extract_headings(doc, baseline_size)
        print(f"Found {len(headings)} heading candidates")
        
        # Print first few headings for debugging
        if headings:
            print("\nFirst few headings found:")
            for h in headings[:10]:
                print(f"  - '{h['text']}' (size: {h['size']:.1f}, page: {h['page']})")
        
        print("Organizing hierarchy...")
        hierarchical_headings = group_by_hierarchy(headings)
        
        print("Saving TOC...")
        save_toc(hierarchical_headings, OUTPUT_PATH)
        
        print(f"Done! Created TOC with {len(hierarchical_headings)} entries")
        doc.close()
        
    except Exception as e:
        print(f"Error processing PDF: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()