import os
from pypdf import PdfReader
from docx import Document


def extract_text(file_path):
    extension = os.path.splitext(file_path)[1].lower()

    if extension == ".pdf":
        return extract_pdf_text(file_path)

    elif extension == ".docx":
        return extract_docx_text(file_path)

    else:
        return ""


def extract_pdf_text(file_path):
    text = ""

    reader = PdfReader(file_path)

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text


def extract_docx_text(file_path):
    text = ""

    document = Document(file_path)

    for paragraph in document.paragraphs:
        text += paragraph.text + "\n"

    return text