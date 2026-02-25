import PyPDF2
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
import io

def create_pdf_from_text(input_file, output_file):
    """
    Reads text from input.txt and creates a PDF file using PyPDF2
    """
    
    # Read the input text file
    try:
        with open(input_file, 'r', encoding='utf-8') as file:
            text_content = file.read()
    except FileNotFoundError:
        print(f"Error: {input_file} not found!")
        return
    except Exception as e:
        print(f"Error reading file: {e}")
        return
    
    # Create a PDF using reportlab (since PyPDF2 doesn't create PDFs from scratch)
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    
    # Set up the page dimensions
    width, height = letter
    
    # Add text to the PDF
    y_position = height - inch  # Start from top with 1 inch margin
    line_height = 14  # Space between lines
    
    # Split text into lines and add to PDF
    lines = text_content.split('\n')
    for line in lines:
        if y_position < inch:  # Check if we need a new page
            can.showPage()
            y_position = height - inch
        
        can.drawString(inch, y_position, line)
        y_position -= line_height
    
    can.save()
    
    # Move to the beginning of the BytesIO buffer
    packet.seek(0)
    
    # Create a new PDF with PyPDF2
    try:
        # Read the generated PDF
        new_pdf = PyPDF2.PdfReader(packet)
        
        # Create a PDF writer
        pdf_writer = PyPDF2.PdfWriter()
        
        # Add all pages from the new PDF
        for page_num in range(len(new_pdf.pages)):
            page = new_pdf.pages[page_num]
            pdf_writer.add_page(page)
        
        # Write to output file
        with open(output_file, 'wb') as output:
            pdf_writer.write(output)
        
        print(f"Successfully created {output_file}")
        
    except Exception as e:
        print(f"Error creating PDF: {e}")

if __name__ == "__main__":
    # Define input and output files
    input_filename = "/content/drive/MyDrive/input.txt"
    output_filename = "/content/drive/MyDrive/output.pdf"
    
    # Create the PDF
    create_pdf_from_text(input_filename, output_filename)