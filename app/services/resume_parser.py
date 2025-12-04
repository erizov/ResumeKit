"""
Utilities for extracting text from uploaded resume files.

The extracted plain text is later converted to structured data by LLM
prompts or additional parsing logic.
"""

from typing import Final
import io

import pdfplumber
from docx import Document
from fastapi import UploadFile


_DOCX_MIME_TYPES: Final = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
}

_PDF_MIME_TYPES: Final = {"application/pdf"}


async def extract_text_from_upload(file: UploadFile) -> str:
    """
    Extract plain text from an uploaded resume file.

    For DOCX files the python-docx library is used. For PDF files the
    pdfplumber library is used. Other file types fall back to decoding
    the raw bytes as UTF-8.
    """
    if file.content_type in _DOCX_MIME_TYPES or file.filename.endswith(
        (".docx", ".doc")
    ):
        return await _extract_docx(file)

    if file.content_type in _PDF_MIME_TYPES or file.filename.endswith(".pdf"):
        return await _extract_pdf(file)

    data = await file.read()
    return data.decode("utf-8", errors="ignore")


async def _extract_docx(file: UploadFile) -> str:
    """
    Extract text from a DOCX file.
    """
    data = await file.read()
    document = Document(io.BytesIO(data))
    paragraphs = [p.text for p in document.paragraphs if p.text]
    return "\n".join(paragraphs)


async def _extract_pdf(file: UploadFile) -> str:
    """
    Extract text from a PDF file.

    If the file is not a valid PDF, falls back to decoding as UTF-8 text.
    """
    data = await file.read()
    try:
        text_chunks: list[str] = []
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text_chunks.append(page_text)
        result = "\n".join(text_chunks)
        # If PDF parsing produced no text, fall back to plain text.
        if not result.strip():
            return data.decode("utf-8", errors="ignore")
        return result
    except Exception:
        # If PDF parsing fails (invalid PDF, corrupted, etc.),
        # fall back to treating bytes as plain text.
        return data.decode("utf-8", errors="ignore")



