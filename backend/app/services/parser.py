# app/services/parser.py

import logging
import tempfile
import numpy as np
import easyocr
import torch
import fitz

from docling.document_converter import DocumentConverter


logger = logging.getLogger(__name__)


USE_GPU = torch.cuda.is_available()

reader = easyocr.Reader(
    ["en"],
    gpu=USE_GPU,
    model_storage_directory="./models"
)


def extract_text_with_ocr(file_bytes: bytes):
    try:
        document = fitz.open(
            stream=file_bytes,
            filetype="pdf"
        )

        full_text = ""

        for page in document:
            matrix = fitz.Matrix(2.5, 2.5)

            pix = page.get_pixmap(
                matrix=matrix
            )

            image = np.frombuffer(
                pix.samples,
                dtype=np.uint8
            )

            image = image.reshape(
                pix.height,
                pix.width,
                pix.n
            )

            results = reader.readtext(
                image,
                detail=0,
                paragraph=True,
                batch_size=8
            )

            page_text = " ".join(results)

            full_text += page_text + "\n"

        return full_text

    except Exception as error:
        logger.error(
            f"OCR failed: {str(error)}"
        )

        return ""


def extract_text_from_file(
    file_bytes: bytes,
    filename: str
):
    try:
        converter = DocumentConverter()

        suffix = filename.split(".")[-1].lower()

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=f".{suffix}"
        ) as temp_file:

            temp_file.write(file_bytes)
            temp_path = temp_file.name

        result = converter.convert(temp_path)

        text = result.document.export_to_text()

        if not text.strip() and suffix == "pdf":
            text = extract_text_with_ocr(
                file_bytes
            )

        if not text.strip():
            raise ValueError(
                "Unable to extract text"
            )

        return text

    except Exception as error:
        logger.error(
            f"Extraction failed: {str(error)}"
        )

        raise ValueError(
            "Invalid or unsupported file"
        )
