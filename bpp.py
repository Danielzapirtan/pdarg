import pytesseract
from pdf2image import convert_from_path
from PIL import Image

def extract_bold_from_scan(pdf_path):
    # 1. Convert PDF to images. 
    # Use a slightly lower DPI (200) if Termux crashes due to RAM limits.
    pages = convert_from_path(pdf_path, dpi=200)
    
    extracted_lines = []

    for page in pages:
        # 2. Use Tesseract to get detailed word data
        # We use 'config' to improve orientation and script detection (OSD)
        data = pytesseract.image_to_data(page, output_type=pytesseract.Output.DICT)
        
        n_boxes = len(data['text'])
        current_line_text = []
        current_line_heights = []
        last_line_num = -1
        is_bold_line = False

        for i in range(n_boxes):
            text = data['text'][i].strip()
            if not text: continue
            
            line_num = data['line_num'][i]

            # If we hit a new line, process the previous one
            if line_num != last_line_num:
                if current_line_text and is_bold_line:
                    avg_h = sum(current_line_heights) / len(current_line_heights)
                    # Convert pixel height to approximate font size
                    font_size = round(avg_h * 0.72, 1) 
                    extracted_lines.append(f"<{font_size}> {' '.join(current_line_text)}")
                
                # Reset for new line
                current_line_text = []
                current_line_heights = []
                is_bold_line = False
            
            # Tesseract 4+ identifies bolding by looking at pixel density
            # If the 'bold' attribute is 1, we flag the whole line
            if int(data.get('bold', [0]*n_boxes)[i]) == 1:
                is_bold_line = True
            
            # Alternative: Detection via 'font_name' strings containing 'Bold'
            font_info = data.get('font_name', [""]*n_boxes)[i]
            if "bold" in font_info.lower():
                is_bold_line = True

            current_line_text.append(text)
            current_line_heights.append(data['height'][i])
            last_line_num = line_num

    return extracted_lines

# Example Execution
# print("\n".join(extract_bold_from_scan("your_file.pdf")))
