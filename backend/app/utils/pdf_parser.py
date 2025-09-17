"""
PDF parsing utilities.
"""
import re
from pathlib import Path
from typing import Optional, Tuple

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False


def extract_text_from_pdf(file_path: str) -> Tuple[str, int, int]:
    """
    Extract text from PDF file.

    Returns:
        Tuple of (text_content, word_count, page_count)
    """
    file_path_obj = Path(file_path)

    if not file_path_obj.exists():
        raise FileNotFoundError(f"PDF file not found: {file_path}")

    text_content = ""
    page_count = 0

    try:
        if PDFPLUMBER_AVAILABLE:
            # Use pdfplumber for better text extraction
            with pdfplumber.open(file_path) as pdf:
                page_count = len(pdf.pages)
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_content += page_text + "\n\n"

        elif PYPDF2_AVAILABLE:
            # Fallback to PyPDF2
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                page_count = len(pdf_reader.pages)

                for page_num in range(page_count):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    if page_text:
                        text_content += page_text + "\n\n"
        else:
            raise ImportError("Neither pdfplumber nor PyPDF2 is available")

    except Exception as e:
        raise Exception(f"Failed to extract text from PDF: {str(e)}")

    # Clean up the text
    text_content = clean_extracted_text(text_content)

    # Count words
    word_count = len(text_content.split())

    return text_content, word_count, page_count


def extract_text_from_txt(file_path: str) -> Tuple[str, int, int]:
    """
    Extract text from TXT file.

    Returns:
        Tuple of (text_content, word_count, page_count)
    """
    file_path_obj = Path(file_path)

    if not file_path_obj.exists():
        raise FileNotFoundError(f"TXT file not found: {file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            text_content = file.read()
    except UnicodeDecodeError:
        # Try with different encoding
        with open(file_path, 'r', encoding='latin-1') as file:
            text_content = file.read()

    # Clean up the text
    text_content = clean_extracted_text(text_content)

    # Count words
    word_count = len(text_content.split())

    # For text files, we consider it as 1 page
    page_count = 1

    return text_content, word_count, page_count


def clean_extracted_text(text: str) -> str:
    """
    Clean and normalize extracted text.
    """
    if not text:
        return ""

    # Remove excessive whitespace
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)

    # Remove excessive spaces
    text = re.sub(r' +', ' ', text)

    # Strip leading/trailing whitespace
    text = text.strip()

    return text


def extract_text_from_file(file_path: str, file_type: str) -> Tuple[str, int, int]:
    """
    Extract text from file based on type.

    Args:
        file_path: Path to the file
        file_type: Type of file ('pdf', 'txt', 'doc')

    Returns:
        Tuple of (text_content, word_count, page_count)
    """
    if file_type == 'pdf':
        return extract_text_from_pdf(file_path)
    elif file_type == 'txt':
        return extract_text_from_txt(file_path)
    elif file_type in ['doc', 'docx']:
        # For now, we'll treat doc files as text files
        # In a production system, you'd use libraries like python-docx
        return extract_text_from_txt(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")


def get_file_info(file_path: str) -> dict:
    """
    Get basic information about a file.
    """
    path_obj = Path(file_path)

    if not path_obj.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    return {
        "filename": path_obj.name,
        "size": path_obj.stat().st_size,
        "modified": path_obj.stat().st_mtime,
        "extension": path_obj.suffix
    }