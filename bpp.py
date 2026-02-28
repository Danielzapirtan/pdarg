import pytesseract
from pdf2image import convert_from_path
from PIL import Image, ImageEnhance

def extract_bold_from_pixels(pdf_path):
    # 1. Convert PDF to high-res images (300-600 DPI is best for pixelated text)
    pages = convert_from_path(pdf_path, dpi=300)
    
    extracted_report = []

    for page in pages:
        # 2. Pre-process: Increase contrast to make bold stand out
        enhancer = ImageEnhance.Contrast(page)
        processed_page = enhancer.enhance(2.0) # Double the contrast
        
        # 3. Get OCR data with 'config' to help detect styles
        # We use 'config' to tell Tesseract to look for hOCR attributes
        data = pytesseract.image_to_data(processed_page, output_type=pytesseract.Output.DICT)
        
        n_boxes = len(data['text'])
        line_map = {} # Groups text by their vertical position (y-coordinate)

        for i in range(n_boxes):
            text = data['text'][i].strip()
            if not text:
                continue

            # In image-based PDFs, 'top' coordinate defines the line
            y_pos = data['top'][i]
            # Group by approximate Y-coordinate (tolerance of 10 pixels)
            line_key = y_pos // 10 
            
            if line_key not in line_map:
                line_map[line_key] = {'text': [], 'heights': [], 'is_bold': False}

            # Tesseract's 'weight' or 'bold' detection in image_to_data
            # Note: This depends on the Tesseract version and 'config'
            if 'bold' in data and data['bold'][i] == 1:
                line_map[line_key]['is_bold'] = True
            
            # Fallback: If Tesseract doesn't flag it, we check the stroke height
            # Bold letters often have a slightly different height/width ratio
            line_map[line_key]['text'].append(text)
            line_map[line_key]['heights'].append(data['height'][i])

        # 4. Filter for lines that are significantly taller/bold
        for key in sorted(line_map.keys()):
            line_data = line_map[key]
            # Heuristic: If Tesseract flagged it OR text is unusually large
            if line_data['is_bold'] or max(line_data['heights']) > 25: 
                avg_height = sum(line_data['heights']) / len(line_data['heights'])
                # Convert pixel height to approximate font size (px * 0.72)
                font_size = round(avg_height * 0.72, 1)
                
                content = " ".join(line_data['text'])
                extracted_report.append(f"<{font_size}> {content}")

    return extracted_report

# Usage
# report = extract_bold_from_pixels("my_scanned_file.pdf")
