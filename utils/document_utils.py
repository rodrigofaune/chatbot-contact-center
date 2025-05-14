import io
import os
from googleapiclient.http import MediaIoBaseDownload
from drive_utils import get_drive_service
import pdfplumber
import docx

def download_file_from_drive(file_id, destination_path):
    service = get_drive_service()
    request = service.files().get_media(fileId=file_id)
    fh = io.FileIO(destination_path, 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    fh.close()
    return destination_path

def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

def extract_text_from_docx(docx_path):
    doc = docx.Document(docx_path)
    text = "\n".join([p.text for p in doc.paragraphs])
    return text

def extract_text_from_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext in [".docx"]:
        return extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Tipo de archivo no soportado para extracción de texto: {ext}")

def download_and_extract_text_from_pdf_drive(file_id):
    service = get_drive_service()
    request = service.files().get_media(fileId=file_id)
    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    buffer.seek(0)
    text = ""
    with pdfplumber.open(buffer) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text 