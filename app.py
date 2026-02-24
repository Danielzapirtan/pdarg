import pdfplumber
from collections import defaultdict
import re

# Hardcoded path to your PDF
PDF_PATH = "/content/drive/MyDrive/input.pdf"
OUTPUT_PATH = "/content/drive/MyDrive/table_of_contents.txt"

def get_baseline_font_size(pdf):
    """Determine the most common font size for regular text"""
    font_sizes = []
    
    for page in pdf.pages:
        for word in page.extract_words(keep_blank_chars=False, use_text_flow=True):
            if 'size' in word:
                font_sizes.append(word['size'])
    
    # Return the most frequent size as baseline
    if font_sizes:
        return max(set(font_sizes), key=font_sizes.count)
    return 10  # Default fallback

def is_bold(fontname):
    """Check if font is bold based on common naming patterns"""
    fontname = fontname.lower()
    bold_indicators = ['bold', 'bd', 'black', 'heavy', 'demi']
    return any(indicator in fontname for indicator in bold_indicators)

def extract_headings(pdf, baseline_size):
    """Extract all bold text with size > baseline"""
    headings = []
    
    for page_num, page in enumerate(pdf.pages, 1):
        words = page.extract_words(keep_blank_chars=False, use_text_flow=True)
        
        # Group words that might be part of same heading
        current_heading = None
        
        for word in words:
            fontname = word.get('fontname', '')
            size = word.get('size', 0)
            
            # Check if this is a heading candidate
            if is_bold(fontname) and size > baseline_size * 1.1:  # 10% threshold
                if current_heading and abs(word['top'] - current_heading['top']) < 5:  # Same line
                    current_heading['text'] += ' ' + word['text']
                else:
                    if current_heading:
                        headings.append(current_heading)
                    current_heading = {
                        'text': word['text'],
                        'size': size,
                        'page': page_num,
                        'top': word['top']
                    }
            else:
                if current_heading:
                    headings.append(current_heading)
                    current_heading = None
        
        # Don't forget last heading on page
        if current_heading:
            headings.append(current_heading)
    
    return headings

def group_by_hierarchy(headings):
    """Group headings into hierarchical levels based on font size"""
    if not headings:
        return []
    
    # Sort by font size descending to identify unique sizes
    unique_sizes = sorted(set(h['size'] for h in headings), reverse=True)
    
    # Create size to level mapping
    size_to_level = {size: i+1 for i, size in enumerate(unique_sizes)}
    
    # Assign levels and track hierarchy
    hierarchical_headings = []
    level_stack = []
    
    for heading in sorted(headings, key=lambda x: (x['page'], x['top'])):
        level = size_to_level[heading['size']]
        
        # Adjust stack for current level
        while level_stack and level_stack[-1] >= level:
            level_stack.pop()
        level_stack.append(level)
        
        hierarchical_headings.append({
            'text': heading['text'].strip(),
            'level': level,
            'page': heading['page'],
            'indent': '   ' * (level - 1)
        })
    
    return hierarchical_headings

def save_toc(headings, output_path):
    """Save hierarchical TOC to text file"""
    with open(output_path, 'w', encoding='utf-8') as f:
        for heading in headings:
            # Create the TOC line with dots and page number
            text = heading['text']
            indent = heading['indent']
            page = heading['page']
            
            # Calculate dots for alignment (target 60 chars total)
            dots_count = max(1, 55 - len(indent) - len(text) - len(str(page)))
            dots = '.' * dots_count
            
            line = f"{indent}{text} {dots} {page}\n"
            f.write(line)
    
    print(f"TOC saved to {output_path}")

def main():
    print(f"Processing PDF: {PDF_PATH}")
    
    try:
        with pdfplumber.open(PDF_PATH) as pdf:
            print("Analyzing document...")
            baseline_size = get_baseline_font_size(pdf)
            print(f"Baseline font size: {baseline_size:.1f}")
            
            print("Extracting headings...")
            headings = extract_headings(pdf, baseline_size)
            print(f"Found {len(headings)} heading candidates")
            
            print("Organizing hierarchy...")
            hierarchical_headings = group_by_hierarchy(headings)
            
            print("Saving TOC...")
            save_toc(hierarchical_headings, OUTPUT_PATH)
            
            print(f"Done! Created TOC with {len(hierarchical_headings)} entries")
            
    except Exception as e:
        print(f"Error processing PDF: {e}")

if __name__ == "__main__":
    main()