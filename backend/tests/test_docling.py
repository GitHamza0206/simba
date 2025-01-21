from docling.document_converter import DocumentConverter
from markitdown import MarkItDown


source = "../uploads/modele-de-compte-de-resultat-en-tableau.pdf"  # document per local path or URL
converter = DocumentConverter()
result = converter.convert(source)
print(result.document.export_to_markdown())  # output: "## Docling Technical Report[...]"
