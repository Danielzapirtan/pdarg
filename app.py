import PyPDF2
import re
import os
from pathlib import Path
import json
from typing import List, Dict, Any

def extract_toc_from_pdf(
    pdf_path: str, 
    header_pattern: str = r'^([A-Z][A-Z\s\-]+|\d+\.\s+.*)$',
    min_length: int = 5,
    output_format: str = 'text'  # 'text', 'json', or 'both'
) -> List[Dict[str, Any]]:
    """
    Extract potential TOC entries from PDF text
    
    Args:
        pdf_path: Path to the PDF file
        header_pattern: Regex pattern to identify headers
        min_length: Minimum characters for a line to be considered a header
        output_format: Format of the output ('text', 'json', or 'both')
    
    Returns:
        List of dictionaries with TOC entries
    """
    try:
        # Read PDF
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            toc_entries = []
            
            print(f"Processing {len(pdf_reader.pages)} pages...")
            
            # Extract text from each page
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                
                if text:
                    lines = text.split('\n')
                    for line in lines:
                        line = line.strip()
                        if len(line) >= min_length:
                            # Look for patterns that might be TOC entries
                            # Format: "Section Title / XX" or "XX. Section Title" or "Section Title XX"
                            if re.match(header_pattern, line):
                                # Try to extract page number from the end
                                page_match = re.search(r'(\d+)$', line)
                                if page_match:
                                    title = line[:page_match.start()].strip()
                                    page_no = page_match.group(1)
                                    toc_entries.append({
                                        'title': title,
                                        'page': page_no,
                                        'source_page': page_num + 1
                                    })
                                else:
                                    # Check if it's in format "XX / Title"
                                    slash_match = re.match(r'^(\d+)\s*/\s*(.+)$', line)
                                    if slash_match:
                                        toc_entries.append({
                                            'title': slash_match.group(2),
                                            'page': slash_match.group(1),
                                            'source_page': page_num + 1
                                        })
            
            print(f"Found {len(toc_entries)} potential TOC entries")
            return toc_entries
            
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
        return []

def format_toc_as_text(
    toc_entries: List[Dict[str, Any]], 
    include_page_numbers: bool = True,
    sort_by_page: bool = True
) -> str:
    """
    Format TOC entries as text with proper formatting
    
    Args:
        toc_entries: List of TOC entries
        include_page_numbers: Whether to include page numbers
        sort_by_page: Whether to sort entries by page number
    
    Returns:
        Formatted text string
    """
    if not toc_entries:
        return "No table of contents entries found."
    
    # Sort by page number if requested
    if sort_by_page:
        sorted_entries = sorted(
            toc_entries, 
            key=lambda x: int(x['page']) if x['page'].isdigit() else 9999
        )
    else:
        sorted_entries = toc_entries
    
    lines = []
    for entry in sorted_entries:
        if include_page_numbers:
            # Format: "Title / Page"
            lines.append(f"{entry['title']} / {entry['page']}")
        else:
            lines.append(entry['title'])
    
    return '\n'.join(lines)

def save_toc_to_file(
    toc_entries: List[Dict[str, Any]], 
    output_path: str,
    format_type: str = 'text'  # 'text' or 'json'
) -> None:
    """
    Save TOC entries to a file
    
    Args:
        toc_entries: List of TOC entries
        output_path: Path to save the file
        format_type: 'text' or 'json'
    """
    if format_type == 'json':
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(toc_entries, f, indent=2, ensure_ascii=False)
    else:  # text
        text_toc = format_toc_as_text(toc_entries)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text_toc)
    
    print(f"Saved TOC to {output_path}")

def organize_toc_hierarchically(
    toc_entries: List[Dict[str, Any]]
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Organize TOC entries into a hierarchical structure
    
    Args:
        toc_entries: List of TOC entries
    
    Returns:
        Dictionary with hierarchical organization
    """
    hierarchy = {}
    
    for entry in toc_entries:
        # Try to identify main sections (e.g., PART I, Chapter 1)
        main_match = re.match(r'^(PART\s+[IVX]+|[A-Z\s]{5,})', entry['title'], re.IGNORECASE)
        if main_match:
            main_section = main_match.group(1)
            if main_section not in hierarchy:
                hierarchy[main_section] = []
            hierarchy[main_section].append(entry)
        else:
            # Check for chapter numbers
            chapter_match = re.match(r'^(\d+\.)\s+(.+)$', entry['title'])
            if chapter_match:
                chapter_num = chapter_match.group(1)
                if chapter_num not in hierarchy:
                    hierarchy[chapter_num] = []
                hierarchy[chapter_num].append(entry)
            else:
                if "Other" not in hierarchy:
                    hierarchy["Other"] = []
                hierarchy["Other"].append(entry)
    
    return hierarchy

def print_toc_hierarchical(
    hierarchy: Dict[str, List[Dict[str, Any]]]
) -> None:
    """
    Print TOC in a hierarchical format
    
    Args:
        hierarchy: Dictionary with hierarchical organization
    """
    for section, entries in hierarchy.items():
        print(f"\n📌 {section}")
        print("-" * 50)
        for entry in entries:
            print(f"  • {entry['title']} [p. {entry['page']}] (found on p. {entry['source_page']})")

def process_pdf_toc(
    input_path: str,
    output_path: str = None,
    header_pattern: str = r'^([A-Z][A-Z\s\-]+|\d+\.\s+.*)$',
    min_length: int = 5,
    output_formats: List[str] = ['text']
) -> None:
    """
    Main function to process PDF and extract TOC
    
    Args:
        input_path: Path to input PDF file
        output_path: Path for output file (optional)
        header_pattern: Regex pattern to identify headers
        min_length: Minimum header length
        output_formats: List of output formats ['text', 'json', 'both']
    """
    # Check if input file exists
    if not os.path.exists(input_path):
        print(f"Error: Input file '{input_path}' not found")
        return
    
    # Generate output path if not provided
    if output_path is None:
        base_name = Path(input_path).stem
        output_path = str(Path(input_path).parent / f"{base_name}_toc")
    
    print(f"Processing PDF: {input_path}")
    print("-" * 50)
    
    # Extract TOC entries
    toc_entries = extract_toc_from_pdf(
        input_path,
        header_pattern=header_pattern,
        min_length=min_length
    )
    
    if not toc_entries:
        print("No TOC entries found. Try adjusting parameters.")
        return
    
    # Display results
    print(f"\nFound {len(toc_entries)} TOC entries:")
    print("-" * 50)
    
    # Text format
    if 'text' in output_formats or 'both' in output_formats:
        text_toc = format_toc_as_text(toc_entries)
        print("\n📝 Text Format:")
        print(text_toc)
        
        # Save to file
        text_output = f"{output_path}.txt"
        save_toc_to_file(toc_entries, text_output, 'text')
    
    # JSON format
    if 'json' in output_formats or 'both' in output_formats:
        json_output = f"{output_path}.json"
        save_toc_to_file(toc_entries, json_output, 'json')
    
    # Hierarchical organization
    print("\n📊 Hierarchical Organization:")
    hierarchy = organize_toc_hierarchically(toc_entries)
    print_toc_hierarchical(hierarchy)

def main():
    """
    Main execution function
    """
    # Define file paths in Google Drive
    drive_path = '/content/drive/MyDrive'
    input_pdf = os.path.join(drive_path, 'input.pdf')
    output_pdf = os.path.join(drive_path, 'toc')  # Will create toc.txt and toc.json
    
    print("PDF Table of Contents Extractor")
    print("=" * 50)
    
    # Check if Google Drive is mounted
    if not os.path.exists(drive_path):
        print(f"Error: Google Drive path '{drive_path}' not found.")
        print("Make sure Google Drive is mounted in Colab with:")
        print("from google.colab import drive")
        print("drive.mount('/content/drive')")
        return
    
    # Process the PDF
    process_pdf_toc(
        input_path=input_pdf,
        output_path=output_pdf,
        header_pattern=r'^([A-Z][A-Z\s\-]+|\d+\.\s+.*)$',  # Default pattern
        min_length=5,
        output_formats=['both']  # Generate both text and JSON
    )
    
    print("\n" + "=" * 50)
    print("Processing complete!")
    print(f"Check {output_pdf}.txt and {output_pdf}.json for results")

if __name__ == "__main__":
    main()