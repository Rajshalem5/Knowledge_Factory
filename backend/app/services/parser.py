import logging
import tempfile

logger = logging.getLogger(__name__)

# Heavy deps loaded lazily so the server starts even if not installed
_reader = None

def _get_reader():
    global _reader
    if _reader is None:
        try:
            import torch
            import easyocr
            USE_GPU = torch.cuda.is_available()
            logger.info(f"GPU Available: {USE_GPU}")
            _reader = easyocr.Reader(
                ['en'],
                gpu=USE_GPU,
                model_storage_directory='./models'
            )
        except ImportError as e:
            raise RuntimeError(
                f"OCR dependencies not installed ({e}). "
                "Run: pip install easyocr torch"
            ) from e
    return _reader


def extract_text_with_ocr(file_bytes: bytes):
    try:
        import numpy as np
        import fitz
        reader = _get_reader()

        doc = fitz.open(stream=file_bytes, filetype="pdf")
        full_text = ""

        for page in doc:
            mat = fitz.Matrix(2.5, 2.5)  # high resolution
            pix = page.get_pixmap(matrix=mat)

            img = np.frombuffer(pix.samples, dtype=np.uint8)
            img = img.reshape(pix.height, pix.width, pix.n)

            results = reader.readtext(
                img,
                detail=0,
                paragraph=True,
                batch_size=8
            )

            page_text = " ".join(results)
            full_text += page_text + "\n"

        return full_text

    except Exception as e:
        logger.error(f"OCR failed: {str(e)}")
        return ""


# 🔹 MAIN extractor (PDF + DOCX + DOC)
def extract_text_from_file(file_bytes: bytes, filename: str):
    try:
        from docling.document_converter import DocumentConverter
        converter = DocumentConverter()

        suffix = filename.split(".")[-1].lower()

    
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{suffix}") as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        result = converter.convert(tmp_path)
        text = result.document.export_to_text()

        
        if not text.strip() and suffix == "pdf":
            logger.info("Docling empty → OCR fallback")
            text = extract_text_with_ocr(file_bytes)

        if not text.strip():
            raise ValueError("Unable to extract text")

        return text

    except Exception as e:
        logger.error(f"Extraction failed: {str(e)}")
        raise ValueError("Invalid or unsupported file")