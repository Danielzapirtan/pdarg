#!/usr/bin/env python3
"""
bpp.py - Big Print Picker
Extracts and prints lines containing characters with bounding box area > threshold.
"""

import json
import sys
from typing import List, Dict, Any, Optional

class BPPProcessor:
    def __init__(self, min_area: float = 100.0):
        """
        Initialize the BPP processor.
        
        Args:
            min_area: Minimum bounding box area threshold
        """
        self.min_area = min_area
        self.large_chars = []
        self.lines_with_large_chars = set()
    
    def calculate_bbox_area(self, bbox: List[float]) -> float:
        """
        Calculate the area of a bounding box.
        
        Args:
            bbox: List of 4 floats [x1, y1, x2, y2]
            
        Returns:
            Area of the bounding box
        """
        if len(bbox) != 4:
            return 0.0
        
        width = abs(bbox[2] - bbox[0])
        height = abs(bbox[3] - bbox[1])
        return width * height
    
    def extract_chars_from_block(self, block: Dict[str, Any], page_num: int) -> List[Dict]:
        """
        Extract character information from a block.
        
        Args:
            block: Block dictionary from PDF JSON
            page_num: Current page number
            
        Returns:
            List of character dictionaries with position and text
        """
        chars = []
        
        # Handle different JSON structures
        if 'lines' in block:
            for line in block['lines']:
                if 'spans' in line:
                    for span in line['spans']:
                        if 'chars' in span:
                            for char in span['chars']:
                                if 'bbox' in char:
                                    chars.append({
                                        'char': char.get('text', ''),
                                        'bbox': char['bbox'],
                                        'page': page_num,
                                        'line_text': line.get('text', ''),
                                        'line_bbox': line.get('bbox', [])
                                    })
        
        return chars
    
    def process_pdf_json(self, pdf_data: Dict[str, Any]) -> None:
        """
        Process PDF JSON data to find large characters.
        
        Args:
            pdf_data: Parsed JSON data from the PDF
        """
        # Handle different JSON structures (pdfplumber, pymupdf, etc.)
        if 'pages' in pdf_data:
            pages = pdf_data['pages']
        elif isinstance(pdf_data, list):
            pages = pdf_data
        else:
            pages = [pdf_data]
        
        for page_num, page in enumerate(pages, 1):
            # Extract blocks from page
            blocks = page.get('blocks', page.get('texts', []))
            
            for block in blocks:
                chars = self.extract_chars_from_block(block, page_num)
                
                for char_info in chars:
                    area = self.calculate_bbox_area(char_info['bbox'])
                    
                    if area > self.min_area:
                        self.large_chars.append({
                            'char': char_info['char'],
                            'area': area,
                            'page': char_info['page'],
                            'bbox': char_info['bbox'],
                            'line_text': char_info['line_text']
                        })
                        
                        if char_info['line_text']:
                            self.lines_with_large_chars.add(
                                f"[Page {char_info['page']}] {char_info['line_text']}"
                            )
    
    def print_results(self, verbose: bool = False) -> None:
        """
        Print the results.
        
        Args:
            verbose: If True, print detailed character information
        """
        if not self.large_chars:
            print(f"No characters found with area > {self.min_area}")
            return
        
        print(f"\n{'='*60}")
        print(f"LARGE CHARACTERS (area > {self.min_area})")
        print(f"{'='*60}\n")
        
        if verbose:
            print("DETAILED CHARACTER LIST:")
            print("-" * 40)
            for i, char_info in enumerate(self.large_chars, 1):
                print(f"{i:3}. '{char_info['char']}' (area: {char_info['area']:.2f}) "
                      f"[Page {char_info['page']}]")
                if char_info['bbox']:
                    print(f"     BBox: {char_info['bbox']}")
            print()
        
        print("LINES CONTAINING LARGE CHARACTERS:")
        print("-" * 40)
        for line in sorted(self.lines_with_large_chars):
            print(line)
        
        print(f"\n{'='*60}")
        print(f"Summary: Found {len(self.large_chars)} large characters "
              f"in {len(self.lines_with_large_chars)} lines")
        print(f"{'='*60}")

def main():
    """Main function to run the BPP processor."""
    # Parse command line arguments
    min_area = 100.0  # Default threshold
    verbose = False
    input_file = "input.json"
    
    for i, arg in enumerate(sys.argv[1:]):
        if arg == "-v" or arg == "--verbose":
            verbose = True
        elif arg == "-t" or arg == "--threshold":
            if i + 1 < len(sys.argv[1:]):
                try:
                    min_area = float(sys.argv[i + 2])
                except ValueError:
                    print(f"Error: Invalid threshold value")
                    sys.exit(1)
        elif arg == "-h" or arg == "--help":
            print_help()
            sys.exit(0)
    
    try:
        # Read input JSON
        with open(input_file, 'r', encoding='utf-8') as f:
            pdf_data = json.load(f)
        
        # Process the data
        processor = BPPProcessor(min_area=min_area)
        processor.process_pdf_json(pdf_data)
        
        # Print results
        processor.print_results(verbose=verbose)
        
    except FileNotFoundError:
        print(f"Error: Could not find {input_file}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {input_file}: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def print_help():
    """Print help information."""
    print("""
bpp.py - Big Print Picker
Extracts and prints lines containing characters with bounding box area > threshold.

Usage: python bpp.py [options]

Options:
  -v, --verbose           Print detailed character information
  -t, --threshold VALUE   Set minimum area threshold (default: 100.0)
  -h, --help              Show this help message

The script reads from input.json in the current directory.
Expected JSON structure should contain pages with blocks containing lines with spans and chars,
each char having a bbox field [x1, y1, x2, y2].
    """)

if __name__ == "__main__":
    main()
