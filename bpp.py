from dedoc.readers import DedocReader

# Initialize the reader
reader = DedocReader()

# Extract structured document
result = reader.extract(file_path="/content/drive/MyDrive/input.pdf")

# Access the document tree structure
document_tree = result.content
# Navigate through headings and lists
for item in document_tree:
    if item.type == "heading":
        print(f"Heading: {item.text}")
    elif item.type == "list_item":
        print(f"List item: {item.text}")
