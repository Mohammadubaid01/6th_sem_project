from pypdf import PdfReader
import os
from striprtf.striprtf import rtf_to_text
from docx import Document


def load_file(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()

    # PDF
    if ext == ".pdf":
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted
        return text

    # TXT
    elif ext == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    # DOCX
    elif ext == ".docx":
        doc = Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])

    # RTF FIXED
    elif ext == ".rtf":
        with open(file_path, "r", encoding="utf-8") as f:
            return rtf_to_text(f.read())

    # Unsupported
    else:
        raise ValueError(f"Unsupported file type: {ext}")






































# from pypdf import PdfReader

# def load_pdf(file_path: str) -> str:
#     reader = PdfReader(file_path)
#     text = ""

#     for page in reader.pages:
#         extracted = page.extract_text()
#         if extracted:
#             text += extracted

#     return text


'''the limitation of this is it only extract simple text, it does not extract 
tables, images, or other complex formatting like scanned text, images etc .'''

'''for scanned text, you can use OCR (Optical Character Recognition) tools like 
Tesseract to extract text from images.

For tables, you can use libraries like Camelot or Tabula to extract tables from 
PDFs.

For images, you can use libraries like PyMuPDF or pdf2image to extract images 
from PDFs.'''


# from pypdf import PdfReader

# def load_pdf(file_path: str) -> str:
#     reader = PdfReader(file_path)
#     text = ""
#     for page in reader.pages:
#         extracted += page.extract_text()
#         if extracted:
#             text += extracted
#     return text