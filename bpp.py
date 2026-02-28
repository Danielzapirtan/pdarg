from pdftext.extraction import dictionary_output

# Get structured data with font information
structured_data = dictionary_output("/home/daniel/input.pdf", sort=True, keep_chars=True)
