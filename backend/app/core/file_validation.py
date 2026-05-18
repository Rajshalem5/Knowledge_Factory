"""
File upload validation — magic bytes, size limits, secure naming.

Uses `filetype` for binary formats (PDF, JPEG, PNG) and manual
content checks for text-based files (CSV).

For production, add ClamAV scanning and a quarantine→scan→release
pipeline. The single most impactful defense is serving files from
a SEPARATE ORIGIN (e.g. files.knowledgefactory.com) so even a
malicious file can't access app cookies/localStorage.
"""

import uuid
from typing import BinaryIO

MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB

# ── Acceptable types for document uploads ──────────────────────────
ALLOWED_MIMES = {
    "application/pdf":         "pdf",
    "image/jpeg":              "jpeg",
    "image/png":               "png",
}

# Text extensions that must pass content sniffing (no magic bytes)
TEXT_EXTENSIONS = {".csv", ".txt", ".json"}


class FileValidationError(ValueError):
    """Raised when a file fails validation."""


def validate_upload(
    filename: str,
    content: bytes,
    *,
    allowed_mimes: dict[str, str] | None = None,
    max_size: int = MAX_UPLOAD_SIZE,
    allow_text: bool = False,
) -> str:
    """Validate file content and return the detected extension.
    
    Raises FileValidationError on any failure.
    Returns the canonical extension (e.g. 'pdf', 'jpeg').
    """
    # 1. Size limit
    if len(content) > max_size:
        raise FileValidationError(
            f"File too large ({len(content) / 1024 / 1024:.1f} MB). "
            f"Maximum is {max_size / 1024 / 1024:.0f} MB."
        )

    if allowed_mimes is None:
        allowed_mimes = ALLOWED_MIMES

    ext = _ext_from_name(filename)

    # 2. Text-based files — decode attempt + extension check
    if ext in TEXT_EXTENSIONS:
        if not allow_text:
            raise FileValidationError(f"Text files (.{ext}) are not accepted here.")
        _validate_text(content, ext)
        return ext

    # 3. Binary files — magic byte detection
    detected = _detect_magic(content)
    if detected is None:
        raise FileValidationError(
            f"Could not detect file type. Accepted: {', '.join(allowed_mimes)}"
        )
    mime, canon_ext = detected
    if mime not in allowed_mimes:
        raise FileValidationError(
            f"File type '{mime}' is not allowed. "
            f"Accepted: {', '.join(allowed_mimes)}"
        )
    return canon_ext


def secure_filename(ext: str) -> str:
    """Generate a UUID-based filename with the given extension."""
    return f"{uuid.uuid4().hex}.{ext}"


# ── Internal helpers ──────────────────────────────────────────────

def _ext_from_name(filename: str) -> str:
    _, ext = (filename or "").rsplit(".", 1)
    return f".{ext.lower()}" if ext else ""


def _validate_text(content: bytes, ext: str) -> None:
    """Ensure text content is valid UTF-8 and not empty."""
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise FileValidationError(
            f"File claims to be .{ext.lstrip('.')} but is not valid UTF-8 text."
        )
    if not text.strip():
        raise FileValidationError("File is empty.")


def _detect_magic(content: bytes):
    """Detect file type from magic bytes using `filetype`."""
    import filetype
    kind = filetype.guess(content)
    if kind is None:
        return None
    return kind.mime, kind.extension
