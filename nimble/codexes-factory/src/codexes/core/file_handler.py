import logging
import fitz  # PyMuPDF
import docx
import json
import traceback
import os
from typing import Optional

def load_document(file_path: str) -> Optional[str]:
    """
    Loads a document from the given path, supporting PDF, DOCX, TXT.
    For PDF, it includes page number markers.
    Returns the content as a string or None if an error occurs.
    """
    logging.info(f"Attempting to load document: {file_path}")
    if not os.path.exists(file_path):
        logging.error(f"File not found: {file_path}")
        return None
        
    try:
        if file_path.lower().endswith('.pdf'):
            return _load_pdf(file_path)
        elif file_path.lower().endswith('.docx'):
            return _load_docx(file_path)
        elif file_path.lower().endswith('.txt'):
            return _load_txt(file_path)
        else:
            raise ValueError(f"Unsupported file format: {os.path.splitext(file_path)[1]}")
    except Exception as e:
        logging.error(f"Failed to load document {file_path}. Error: {e}\n{traceback.format_exc()}")
        return None

def _load_pdf(file_path: str) -> str:
    """Loads text from a PDF file using PyMuPDF, adding page markers."""
    try:
        doc = fitz.open(file_path)
        content = []
        logging.info(f"PDF has {len(doc)} pages.")
        for i, page in enumerate(doc):
            text = page.get_text()
            if text:
                content.append(f"--- PAGE {i + 1} ---\n{text}")
        logging.info(f"Successfully loaded and processed {len(doc)} pages from PDF.")
        return "\n\n".join(content)
    except Exception as e:
        logging.error(f"Failed to read PDF {file_path}: {e}", exc_info=True)
        raise

def _load_docx(file_path: str) -> str:
    """Loads text from a DOCX file."""
    try:
        doc = docx.Document(file_path)
        full_text = [para.text for para in doc.paragraphs]
        logging.info(f"Successfully loaded DOCX file with {len(full_text)} paragraphs.")
        return '\n\n'.join(full_text)
    except Exception as e:
        logging.error(f"Failed to read DOCX {file_path}: {e}", exc_info=True)
        raise

def _load_txt(file_path: str) -> str:
    """Loads text from a TXT file."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        logging.info(f"Successfully loaded TXT file.")
        return content
    except Exception as e:
        logging.error(f"Failed to read TXT {file_path}: {e}", exc_info=True)
        raise