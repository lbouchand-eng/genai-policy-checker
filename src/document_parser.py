"""
Document parser module for extracting text from various file formats.

Supports PDF, DOCX, and TXT files.
"""
import os
import logging
from typing import Optional
import PyPDF2
from docx import Document

from src.exceptions import DocumentParsingError

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from a PDF file.
    
    Args:
        file_path: Path to the PDF file
    
    Returns:
        Extracted text content
    
    Raises:
        DocumentParsingError: If PDF reading fails
    """
    try:
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        logger.error(f"Failed to extract text from PDF {file_path}: {e}")
        raise DocumentParsingError(f"Error reading PDF: {str(e)}")


def extract_text_from_docx(file_path: str) -> str:
    """
    Extract text from a DOCX file.
    
    Args:
        file_path: Path to the DOCX file
    
    Returns:
        Extracted text content
    
    Raises:
        DocumentParsingError: If DOCX reading fails
    """
    try:
        doc = Document(file_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text.strip()
    except Exception as e:
        logger.error(f"Failed to extract text from DOCX {file_path}: {e}")
        raise DocumentParsingError(f"Error reading DOCX: {str(e)}")


def extract_text_from_txt(file_path: str) -> str:
    """
    Extract text from a TXT file.
    
    Args:
        file_path: Path to the TXT file
    
    Returns:
        Extracted text content
    
    Raises:
        DocumentParsingError: If TXT reading fails
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
        return text.strip()
    except Exception as e:
        logger.error(f"Failed to extract text from TXT {file_path}: {e}")
        raise DocumentParsingError(f"Error reading TXT: {str(e)}")


def parse_document(file_path: str) -> str:
    """
    Parse a document and extract its text content.
    
    Supports PDF, DOCX, and TXT formats.
    
    Args:
        file_path: Path to the document file
    
    Returns:
        Extracted text content
    
    Raises:
        DocumentParsingError: If parsing fails
        ValueError: If file format is not supported
    """
    file_ext = os.path.splitext(file_path)[1].lower()
    
    if file_ext == '.pdf':
        return extract_text_from_pdf(file_path)
    elif file_ext in ['.docx', '.doc']:
        return extract_text_from_docx(file_path)
    elif file_ext == '.txt':
        return extract_text_from_txt(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_ext}. Supported formats: PDF, DOCX, TXT")

