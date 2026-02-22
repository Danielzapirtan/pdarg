#!/usr/bin/env python3
"""
PDF Pedagogical Architecture Generator
Adds an extended table of contents with hierarchical structure to a PDF.
"""

import os
import sys
from pathlib import Path
import PyPDF2
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Spacer
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io
import argparse
from datetime import datetime
import fitz  # PyMuPDF for font analysis
from collections import defaultdict

class PedagogicalArchitecture:
    """Main class to generate pedagogical architecture for PDFs"""
    
    # Emoticons for different hierarchy levels
    RANK_EMOTICONS = {
        0: "📚",  # Book level
        1: "📖",  # Chapter level
        2: "📑",  # Section level
        3: "📌",  # Subsection level
        4: "🔹",  # Sub-subsection level
        5: "•",   # Further levels
    }
    
    def __init__(self, input_path, output_path=None):
        self.input_path = Path(input_path)
        if not self.input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        if output_path is None:
            self.output_path = self.input_path.parent / f"pedagogical_{self.input_path.name}"
        else:
            self.output_path = Path(output_path)
        
        self.structure = []
        self.outline = None
        
    def extract_outline(self):
        """Extract existing outline/bookmarks from PDF if available"""
        try:
            doc = fitz.open(self.input_path)
            toc = doc.get_toc()  # Get table of contents
            
            if toc and len(toc) > 0:
                print(f"Found existing outline with {len(toc)} entries")
                self.outline = []
                for level, title, page in toc:
                    # Convert level (1-based in PyMuPDF) to rank (0-based)
                    rank = level - 1
                    self.outline.append({
                        'rank': rank,
                        'title': title,
                        'page': page
                    })
                doc.close()
                return True
            doc.close()
        except Exception as e:
            print(f"Warning: Could not extract outline: {e}")
        
        return False
    
    def analyze_font_structure(self):
        """Analyze font sizes to detect document structure"""
        print("Analyzing font sizes to detect structure...")
        
        try:
            doc = fitz.open(self.input_path)
            font_sizes = []
            text_with_fonts = []
            
            # Extract text with font information
            for page_num in range(len(doc)):
                page = doc[page_num]
                blocks = page.get_text("dict")["blocks"]
                
                for block in blocks:
                    if "lines" in block:
                        for line in block["lines"]:
                            for span in line["spans"]:
                                if span["text"].strip():
                                    font_sizes.append(span["size"])
                                    text_with_fonts.append({
                                        'text': span["text"].strip(),
                                        'size': span["size"],
                                        'page': page_num + 1,
                                        'font': span["font"]
                                    })
            
            doc.close()
            
            if not font_sizes:
                print("No text found for font analysis")
                return False
            
            # Group font sizes and find potential heading sizes
            size_groups = defaultdict(list)
            for item in text_with_fonts:
                # Round to nearest 0.5 for grouping
                rounded_size = round(item['size'] * 2) / 2
                size_groups[rounded_size].append(item)
            
            # Sort sizes by frequency and value
            size_frequencies = {size: len(items) for size, items in size_groups.items()}
            sorted_sizes = sorted(size_frequencies.keys())
            
            # Assume the most frequent size is body text
            body_size = max(size_frequencies, key=size_frequencies.get)
            print(f"Detected body text size: {body_size}")
            
            # Find larger sizes that might be headings
            heading_sizes = [s for s in sorted_sizes if s > body_size]
            heading_sizes.sort(reverse=True)
            
            # Assign ranks to heading sizes (larger = higher rank)
            structure = []
            for i, size in enumerate(heading_sizes[:5]):  # Limit to 5 levels
                rank = i
                items = size_groups[size]
                
                # Group consecutive items that might be the same heading
                current_title = []
                current_page = None
                
                for item in items[:10]:  # Take first few as examples
                    if not current_title or item['page'] == current_page:
                        current_title.append(item['text'])
                        if current_page is None:
                            current_page = item['page']
                    else:
                        if current_title:
                            structure.append({
                                'rank': rank,
                                'title': ' '.join(current_title),
                                'page': current_page
                            })
                        current_title = [item['text']]
                        current_page = item['page']
                
                if current_title:
                    structure.append({
                        'rank': rank,
                        'title': ' '.join(current_title),
                        'page': current_page
                    })
            
            if structure:
                self.structure = structure
                print(f"Detected {len(structure)} potential headings")
                return True
            
        except Exception as e:
            print(f"Error in font analysis: {e}")
        
        return False
    
    def generate_pedagogical_architecture(self):
        """Generate the pedagogical architecture text"""
        architecture = []
        architecture.append("=" * 80)
        architecture.append("📋 PEDAGOGICAL ARCHITECTURE")
        architecture.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        architecture.append("=" * 80)
        architecture.append("")
        architecture.append("This document contains the following hierarchical structure:")
        architecture.append("")
        
        if self.outline:
            print("Using existing outline for structure")
            structure_to_use = self.outline
        elif self.structure:
            print("Using font-analyzed structure")
            structure_to_use = self.structure
        else:
            print("No structure detected - creating minimal architecture")
            structure_to_use = [{
                'rank': 0,
                'title': f"Document: {self.input_path.name}",
                'page': 1
            }]
        
        # Group by page for better readability
        current_page = None
        for item in structure_to_use:
            rank = item['rank']
            title = item['title']
            page = item['page']
            
            # Get emoticon for this rank
            emoticon = self.RANK_EMOTICONS.get(rank, self.RANK_EMOTICONS[5])
            
            # Indent based on rank
            indent = "  " * rank
            
            # Show page changes
            if page != current_page:
                if current_page is not None:
                    architecture.append("")
                architecture.append(f"{indent}[Page {page}]")
                current_page = page
            
            # Add the title with emoticon
            architecture.append(f"{indent}{emoticon} [{rank}] {title}")
        
        architecture.append("")
        architecture.append("=" * 80)
        architecture.append("📝 NOTE: Only the structure is shown above.")
        architecture.append("The complete document content follows below.")
        architecture.append("=" * 80)
        architecture.append("")
        
        return "\n".join(architecture)
    
    def prepend_to_pdf(self, architecture_text):
        """Prepend the architecture text to the original PDF"""
        # Create a temporary PDF with the architecture
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=A4)
        
        # Set up styles
        width, height = A4
        margin = 20 * mm
        
        # Split text into lines and write to canvas
        y = height - margin
        line_height = 5 * mm
        
        for line in architecture_text.split('\n'):
            if y < margin:
                can.showPage()
                y = height - margin
            
            # Handle different text formatting
            if line.startswith("=" * 10):
                can.setFont("Helvetica-Bold", 12)
            elif line.startswith("📋") or line.startswith("📝"):
                can.setFont("Helvetica-Bold", 14)
            elif line.startswith("[Page"):
                can.setFont("Helvetica-Bold", 11)
                can.setFillColorRGB(0.2, 0.4, 0.6)
            else:
                can.setFont("Helvetica", 10)
                can.setFillColorRGB(0, 0, 0)
            
            # Draw the line
            can.drawString(margin, y, line)
            y -= line_height
        
        can.save()
        
        # Move to the beginning of the StringIO buffer
        packet.seek(0)
        
        # Create a new PDF with the architecture and original content
        new_pdf = PyPDF2.PdfReader(packet)
        original_pdf = PyPDF2.PdfReader(self.input_path)
        
        # Create output PDF
        output = PyPDF2.PdfWriter()
        
        # Add architecture pages
        for page in new_pdf.pages:
            output.add_page(page)
        
        # Add original content
        for page in original_pdf.pages:
            output.add_page(page)
        
        # Write to output file
        with open(self.output_path, 'wb') as output_file:
            output.write(output_file)
        
        print(f"\n✅ Pedagogical architecture prepended successfully!")
        print(f"📁 Output saved to: {self.output_path}")
    
    def process(self):
        """Main processing method"""
        print(f"\n🔍 Processing: {self.input_path}")
        
        # Try to extract existing outline first
        if not self.extract_outline():
            print("No existing outline found.")
            # Fall back to font analysis
            if not self.analyze_font_structure():
                print("Could not detect structure from fonts.")
                print("Creating minimal architecture.")
        
        # Generate architecture text
        architecture_text = self.generate_pedagogical_architecture()
        
        # Preview the architecture
        print("\n" + "=" * 60)
        print("ARCHITECTURE PREVIEW (first 10 lines):")
        print("=" * 60)
        preview_lines = architecture_text.split('\n')[:10]
        for line in preview_lines:
            print(line)
        print("..." if len(architecture_text.split('\n')) > 10 else "")
        
        # Prepend to PDF
        self.prepend_to_pdf(architecture_text)

def main():
    parser = argparse.ArgumentParser(
        description='Add pedagogical architecture (extended TOC) to a PDF'
    )
    parser.add_argument(
        'input_pdf',
        help='Path to input PDF file',
        nargs='?',
        default='/content/drive/MyDrive/input.pdf'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output PDF file path (optional)'
    )
    
    args = parser.parse_args()
    
    try:
        # Create processor and run
        processor = PedagogicalArchitecture(args.input_pdf, args.output)
        processor.process()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
