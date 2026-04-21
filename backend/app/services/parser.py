import logging
import tempfile
import numpy as np
import easyocr
import torch
import fitz
from docling.document_converter import DocumentConverter

logger = logging.getLogger(__name__)


USE_GPU = torch.cuda.is_available()
logger.info(f"GPU Available: {USE_GPU}")

reader = easyocr.Reader(
    ['en'],
    gpu=USE_GPU,
    model_storage_directory='./models'
)


def extract_text_with_ocr(file_bytes: bytes):
    try:
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