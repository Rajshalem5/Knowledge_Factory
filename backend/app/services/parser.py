import logging
import tempfile
import os
import io

logger = logging.getLogger(__name__)

# 🔹 MAIN extractor (PDF + DOCX + DOC)
async def extract_text_from_file(file_bytes: bytes, filename: str):
    """
    Extract text from documents.
    Provides detailed logging of failures and missing dependencies.
    """
    suffix = filename.split(".")[-1].lower()
    logger.info(f"[parser] Attempting extraction from {filename} (size: {len(file_bytes)} bytes)")

    try:
        # Try Docling first (if installed)
        try:
            from docling.document_converter import DocumentConverter
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{suffix}") as tmp:
                tmp.write(file_bytes)
                tmp_path = tmp.name

            try:
                converter = DocumentConverter()
                result = converter.convert(tmp_path)
                text = result.document.export_to_text()
                if text.strip():
                    logger.info(f"[parser] Docling successful for {filename}")
                    return text
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
        except ImportError:
            logger.debug("[parser] Docling not installed, trying fallbacks...")

        # Fallback 1: PDF via PyMuPDF or pypdf
        if suffix == "pdf":
            try:
                import fitz # PyMuPDF
                doc = fitz.open(stream=file_bytes, filetype="pdf")
                text = ""
                for page in doc:
                    text += page.get_text()
                if text.strip():
                    logger.info(f"[parser] PyMuPDF successful for {filename}")
                    return text
            except ImportError:
                logger.debug("[parser] PyMuPDF not installed")
            
            try:
                import pypdf
                import io
                reader = pypdf.PdfReader(io.BytesIO(file_bytes))
                text = ""
                for page in reader.pages:
                    text += page.extract_text() or ""
                if text.strip():
                    logger.info(f"[parser] pypdf successful for {filename}")
                    return text
            except ImportError:
                logger.debug("[parser] pypdf not installed")

        # Fallback 2: DOCX via python-docx
        if suffix == "docx":
            try:
                import docx
                import io
                doc = docx.Document(io.BytesIO(file_bytes))
                text = "\n".join([para.text for para in doc.paragraphs])
                if text.strip():
                    logger.info(f"[parser] python-docx successful for {filename}")
                    return text
            except ImportError:
                logger.debug("[parser] python-docx not installed")

        # Final check
        raise ValueError(f"No suitable parser installed for {suffix} files. Please install docling, pymupdf, or python-docx.")

    except Exception as e:
        logger.error(f"[parser] Extraction failed for {filename}: {str(e)}")
        # We re-raise a clear error message
        raise ValueError(f"Parsing failed: {str(e)}")
