import pytesseract
from pdf2image import convert_from_path
import gc # Garbage Collector

def extract_bold_efficiently(pdf_path):
    # 1. Lower DPI to 150 to save 4x the RAM compared to 300 DPI
    # 2. Use 'thread_count' to speed up rendering if your phone has multiple cores
    
    extracted_report = []
    
    # We process pages in small chunks to prevent RAM spikes
    # Using 'first_page' and 'last_page' allows us to loop without loading the whole doc
    from pdfinfo_wrapper import pdfinfo # part of pdf2image
    info = pdfinfo(pdf_path)
    total_pages = int(info["Pages"])

    for i in range(1, total_pages + 1):
        print(f"Processing page {i}/{total_pages}...")
        
        # Load ONLY one page at a time
        page_image = convert_from_path(
            pdf_path, 
            dpi=150, 
            first_page=i, 
            last_page=i,
            use_pdftocairo=True # Often more memory-efficient on Linux/Ubuntu
        )[0]

        # Perform OCR
        data = pytesseract.image_to_data(page_image, output_type=pytesseract.Output.DICT)
        
        # ... (Your bold detection logic from the previous script goes here) ...
        # (For brevity: identify lines, check bold flag, append to extracted_report)
        
        # IMPORTANT: Explicitly delete the image and clear RAM
        del page_image
        gc.collect() 

    return extracted_report
