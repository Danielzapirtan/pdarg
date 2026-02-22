#!/usr/bin/env python3
"""
PDF Pedagogical Architecture Generator
Adds an extended table of contents with hierarchical structure to a PDF.
Processes outlines recursively to maintain proper hierarchy.
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
from typing import List, Dict, Any, Optional

class OutlineNode:
    """Represents a node in the outline hierarchy"""
    
    def __init__(self, title: str, rank: int, page: int, level: int):
        self.title = title
        self.rank = rank  # Our pedagogical rank (0-based)
        self.page = page
        self.level = level  # Original outline level (1-based)
        self.children: List[OutlineNode] = []
        self.parent: Optional[OutlineNode] = None
    
    def add_child(self, child: 'OutlineNode'):
        """Add a child node"""
        child.parent = self
        self.children.append(child)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation"""
        return {
            'title': self.title,
            'rank': self.rank,
            'page': self.page,
            'level': self.level,
            'children': [child.to_dict() for child in self.children]
        }
    
    def flatten(self) -> List[Dict[str, Any]]:
        """Flatten the tree into a list with proper rank propagation"""
        result = [{
            'title': self.title,
            'rank': self.rank,
            'page': self.page
        }]
        
        for child in self.children:
            result.extend(child.flatten())
        
        return result
    
    def print_tree(self, indent: int = 0):
        """Print the tree structure for debugging"""
        print("  " * indent + f"└─ [{self.rank}] {self.title} (p.{self.page})")
        for child in self.children:
            child.print_tree(indent + 1)


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
        
        self.root_nodes: List[OutlineNode] = []
        self.structure = []
        self.outline = None
        
    def process_outline_recursively(self, toc_items: List[tuple]) -> List[OutlineNode]:
        """
        Process outline items recursively to build proper hierarchy.
        
        Args:
            toc_items: List of (level, title, page) tuples from PyMuPDF
            
        Returns:
            List of root OutlineNode objects
        """
        if not toc_items:
            return []
        
        roots = []
        stack = []  # Stack to maintain parent-child relationships
        
        for level, title, page in toc_items:
            # Create node for current item
            # Our rank is level-1 (convert from 1-based to 0-based)
            node = OutlineNode(
                title=title,
                rank=level - 1,
                page=page,
                level=level
            )
            
            # If stack is empty, this is a root node
            if not stack:
                roots.append(node)
                stack = [node]
                continue
            
            # Find the parent by going up the stack
            while stack and stack[-1].level >= level:
                stack.pop()
            
            if stack:
                # Current node is a child of the last node in stack
                stack[-1].add_child(node)
            else:
                # No parent found, this is a root node
                roots.append(node)
            
            # Push current node to stack
            stack.append(node)
        
        return roots
    
    def extract_outline(self):
        """Extract existing outline/bookmarks from PDF recursively"""
        try:
            doc = fitz.open(self.input_path)
            toc = doc.get_toc()  # Get table of contents (already hierarchical)
            
            if toc and len(toc) > 0:
                print(f"Found existing outline with {len(toc)} entries")
                
                # Process recursively to build tree
                self.root_nodes = self.process_outline_recursively(toc)
                
                # Debug: print the tree structure
                print("\n📊 Outline hierarchy detected:")
                for i, root in enumerate(self.root_nodes):
                    print(f"\nRoot {i+1}:")
                    root.print_tree()
                
                # Convert tree to flattened structure for display
                self.outline = []
                for root in self.root_nodes:
                    self.outline.extend(root.flatten())
                
                doc.close()
                return True
            
            doc.close()
        except Exception as e:
            print(f"Warning: Could not extract outline: {e}")
        
        return False
    
    def analyze_font_structure_recursive(self, text_items: List[Dict], 
                                         parent_rank: int = -1, 
                                         level: int = 0) -> List[OutlineNode]:
        """
        Recursively analyze font structure to build hierarchy.
        
        Args:
            text_items: List of text items with font info
            parent_rank: Rank of parent (-1 for root)
            level: Current depth level
            
        Returns:
            List of OutlineNode objects
        """
        if not text_items:
            return []
        
        # Group items by page for context
        nodes = []
        i = 0
        
        while i < len(text_items):
            current_item = text_items[i]
            
            # Look ahead to find potential children
            children_items = []
            j = i + 1
            
            # Find items that might be children (same or smaller font size)
            while j < len(text_items):
                if text_items[j]['size'] <= current_item['size']:
                    # Potential child or sibling
                    if text_items[j]['size'] < current_item['size']:
                        # This is likely a child (smaller font)
                        children_items.append(text_items[j])
                    else:
                        # Same size, break (this will be a sibling)
                        break
                else:
                    # Larger font found - this starts a new section
                    break
                j += 1
            
            # Create node for current item
            node = OutlineNode(
                title=current_item['text'],
                rank=level,  # Use current depth as rank
                page=current_item['page'],
                level=level + 1  # Store 1-based level for consistency
            )
            
            # Recursively process children
            if children_items:
                child_nodes = self.analyze_font_structure_recursive(
                    children_items, 
                    parent_rank=level,
                    level=level + 1
                )
                for child in child_nodes:
                    node.add_child(child)
            
            nodes.append(node)
            
            # Move to next item after this group
            i = j if j > i else i + 1
        
        return nodes
    
    def analyze_font_structure(self):
        """Analyze font sizes to detect document structure recursively"""
        print("Analyzing font sizes to detect structure...")
        
        try:
            doc = fitz.open(self.input_path)
            text_with_fonts = []
            
            # Extract text with font information
            for page_num in range(len(doc)):
                page = doc[page_num]
                blocks = page.get_text("dict")["blocks"]
                
                for block in blocks:
                    if "lines" in block:
                        for line in block["lines"]:
                            for span in line["spans"]:
                                text = span["text"].strip()
                                if text and len(text) > 3:  # Ignore very short text
                                    text_with_fonts.append({
                                        'text': text,
                                        'size': span["size"],
                                        'page': page_num + 1,
                                        'font': span["font"]
                                    })
            
            doc.close()
            
            if not text_with_fonts:
                print("No text found for font analysis")
                return False
            
            # Group by font size and find potential heading sizes
            size_groups = defaultdict(list)
            for item in text_with_fonts:
                rounded_size = round(item['size'] * 2) / 2
                size_groups[rounded_size].append(item)
            
            # Find body text size (most frequent)
            size_frequencies = {size: len(items) for size, items in size_groups.items()}
            body_size = max(size_frequencies, key=size_frequencies.get)
            print(f"Detected body text size: {body_size}")
            
            # Filter out body text and very small text
            heading_candidates = [
                item for item in text_with_fonts 
                if item['size'] > body_size * 1.2  # 20% larger than body
            ]
            
            if not heading_candidates:
                print("No clear heading structure detected")
                return False
            
            # Group heading candidates by approximate size
            heading_groups = defaultdict(list)
            for item in heading_candidates:
                # Group sizes within 1pt of each other
                approx_size = round(item['size'])
                heading_groups[approx_size].append(item)
            
            # Sort heading sizes (largest first)
            heading_sizes = sorted(heading_groups.keys(), reverse=True)
            
            # Build hierarchy recursively
            all_headings = []
            for size in heading_sizes[:5]:  # Limit to 5 levels
                all_headings.extend(heading_groups[size])
            
            # Sort by page and position to maintain document order
            all_headings.sort(key=lambda x: (x['page'], text_with_fonts.index(x)))
            
            # Build recursive structure
            self.root_nodes = self.analyze_font_structure_recursive(all_headings)
            
            # Debug: print the detected hierarchy
            print("\n📊 Font-based hierarchy detected:")
            for i, root in enumerate(self.root_nodes):
                print(f"\nRoot {i+1}:")
                root.print_tree()
            
            # Convert to flattened structure
            self.structure = []
            for root in self.root_nodes:
                self.structure.extend(root.flatten())
            
            return True
            
        except Exception as e:
            print(f"Error in font analysis: {e}")
            import traceback
            traceback.print_exc()
        
        return False
    
    def generate_pedagogical_architecture(self):
        """Generate the pedagogical architecture text recursively"""
        architecture = []
        architecture.append("=" * 80)
        architecture.append("📋 PEDAGOGICAL ARCHITECTURE")
        architecture.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        architecture.append("=" * 80)
        architecture.append("")
        architecture.append("This document contains the following hierarchical structure:")
        architecture.append("")
        
        if self.root_nodes:
            print("\nUsing recursive structure for output")
            # Use the tree structure directly for better formatting
            self._add_tree_to_architecture(architecture, self.root_nodes)
        else:
            print("No structure detected - creating minimal architecture")
            architecture.append(f"📄 Document: {self.input_path.name}")
        
        architecture.append("")
        architecture.append("=" * 80)
        architecture.append("📝 NOTE: Only the structure is shown above.")
        architecture.append("The complete document content follows below.")
        architecture.append("=" * 80)
        architecture.append("")
        
        return "\n".join(architecture)
    
    def _add_tree_to_architecture(self, architecture: List[str], 
                                  nodes: List[OutlineNode], 
                                  indent: int = 0):
        """Recursively add tree nodes to architecture text"""
        for node in nodes:
            # Get emoticon for this rank
            emoticon = self.RANK_EMOTICONS.get(node.rank, self.RANK_EMOTICONS[5])
            
            # Create indentation
            indent_str = "  " * indent
            
            # Add the title with emoticon and page
            architecture.append(
                f"{indent_str}{emoticon} [Rank {node.rank}] {node.title} "
                f"(p. {node.page})"
            )
            
            # Recursively add children
            if node.children:
                self._add_tree_to_architecture(architecture, node.children, indent + 1)
    
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
            elif "[Rank" in line:
                # Hierarchy lines
                can.setFont("Helvetica", 10)
                # Color based on rank (extract rank number)
                try:
                    rank_start = line.find("[Rank") + 6
                    rank_end = line.find("]", rank_start)
                    rank = int(line[rank_start:rank_end].strip())
                    # Different colors for different ranks
                    colors = [(0,0,0), (0.2,0.4,0.6), (0.1,0.5,0.1), 
                             (0.6,0.3,0.1), (0.5,0.2,0.5)]
                    if rank < len(colors):
                        can.setFillColorRGB(*colors[rank])
                except:
                    can.setFillColorRGB(0, 0, 0)
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
        
        # Print statistics
        total_nodes = sum(len(root.flatten()) for root in self.root_nodes)
        print(f"📊 Total hierarchical elements: {total_nodes}")
        print(f"📊 Hierarchy depth: {max((len(root.flatten()) for root in self.root_nodes), default=0)}")
    
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
                # Create a minimal root node
                self.root_nodes = [OutlineNode(
                    title=f"Document: {self.input_path.name}",
                    rank=0,
                    page=1,
                    level=1
                )]
        
        # Generate architecture text
        architecture_text = self.generate_pedagogical_architecture()
        
        # Preview the architecture
        print("\n" + "=" * 60)
        print("ARCHITECTURE PREVIEW (first 15 lines):")
        print("=" * 60)
        preview_lines = architecture_text.split('\n')[:15]
        for line in preview_lines:
            print(line)
        print("..." if len(architecture_text.split('\n')) > 15 else "")
        
        # Ask for confirmation
        response = input("\nProceed with prepending? (y/n): ").lower()
        if response == 'y':
            self.prepend_to_pdf(architecture_text)
        else:
            print("Operation cancelled.")

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
    parser.add_argument(
        '-y', '--yes',
        action='store_true',
        help='Skip confirmation prompt'
    )
    
    args = parser.parse_args()
    
    try:
        # Create processor and run
        processor = PedagogicalArchitecture(args.input_pdf, args.output)
        processor.process()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()