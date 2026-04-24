import logging
import uuid
from dataclasses import dataclass
from pathlib import Path

import aiofiles
from fastapi import UploadFile

from src.api.constants import ALLOWED_EXTENSIONS, ALLOWED_MIME_TYPES

logger = logging.getLogger(__name__)

_CHUNK_SIZE = 64 * 1024  # 64 KiB


class UnsupportedMediaTypeError(Exception):
    """Raised when the uploaded file's MIME type is not allowed."""


class FileTooLargeError(Exception):
    """Raised when the uploaded file exceeds the configured size limit."""


class EmptyFileError(Exception):
    """Raised when the uploaded file has no content."""


@dataclass(frozen=True)
class StoredImage:
    path: Path
    mime_type: str


async def store_uploaded_image(
    *,
    file: UploadFile,
    uploads_dir: Path,
    max_bytes: int,
) -> StoredImage:
    """Validate and persist an uploaded image to disk.

    Reads the file in chunks to enforce the size limit without buffering
    the entire payload in memory.

    Args:
        file: The multipart upload received by FastAPI.
        uploads_dir: Directory where the file will be saved.
        max_bytes: Maximum allowed file size in bytes.

    Returns:
        StoredImage with the final path and detected MIME type.

    Raises:
        UnsupportedMediaTypeError: MIME type is not in ALLOWED_MIME_TYPES.
        EmptyFileError: File has zero bytes.
        FileTooLargeError: File exceeds max_bytes.
    """
    mime = file.content_type or ""
    if mime not in ALLOWED_MIME_TYPES:
        raise UnsupportedMediaTypeError(mime)

    ext = ALLOWED_EXTENSIONS[mime]
    dest = uploads_dir / f"{uuid.uuid4()}.{ext}"
    tmp = dest.with_suffix(".tmp")

    uploads_dir.mkdir(parents=True, exist_ok=True)

    total = 0
    try:
        async with aiofiles.open(tmp, "wb") as fh:
            while chunk := await file.read(size=_CHUNK_SIZE):
                total += len(chunk)
                if total > max_bytes:
                    raise FileTooLargeError(f"{total} bytes exceeds limit of {max_bytes}")
                await fh.write(chunk)
    except (UnsupportedMediaTypeError, FileTooLargeError, EmptyFileError):
        tmp.unlink(missing_ok=True)
        raise
    except Exception:
        tmp.unlink(missing_ok=True)
        raise

    if total == 0:
        tmp.unlink(missing_ok=True)
        raise EmptyFileError("Uploaded file is empty")

    tmp.rename(dest)
    logger.info("stored upload: path=%s mime=%s bytes=%d", dest, mime, total)
    return StoredImage(path=dest, mime_type=mime)
