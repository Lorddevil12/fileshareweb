from PyPDF2 import PdfReader
from docx import Document

def convert_pdf_to_docx(input_path, output_path):
    pdf = PdfReader(input_path)
    doc = Document()
    
    for page in pdf.pages:
        doc.add_paragraph(page.extract_text())
    
    doc.save(output_path)
