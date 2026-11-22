from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings
from app.core.errors import ServiceError

_CHUNK = 1024 * 1024


def ensure_dirs() -> None:
    settings.pdf_dir.mkdir(parents=True, exist_ok=True)
    settings.cover_dir.mkdir(parents=True, exist_ok=True)


def pdf_path(filename: str) -> Path:
    return settings.pdf_dir / filename


def cover_path(filename: str) -> Path:
    return settings.cover_dir / filename


def safe_delete(*paths: Path) -> None:
    for p in paths:
        try:
            p.unlink(missing_ok=True)
        except OSError:
            pass


def save_pdf_upload(upload: UploadFile, dest: Path) -> int:
    """Stream an uploaded PDF to disk, enforcing the PDF signature and size limit."""
    max_bytes = settings.max_pdf_bytes
    upload.file.seek(0)
    head = upload.file.read(5)
    if head != b"%PDF-":
        raise ServiceError("The uploaded file is not a PDF.", 400)

    size = len(head)
    try:
        with dest.open("wb") as out:
            out.write(head)
            while chunk := upload.file.read(_CHUNK):
                size += len(chunk)
                if size > max_bytes:
                    raise ServiceError(f"PDF is larger than {settings.max_pdf_size_mb} MB.", 413)
                out.write(chunk)
    except BaseException:
        safe_delete(dest)
        raise
    return size


def read_image_upload(upload: UploadFile) -> bytes:
    max_bytes = settings.max_image_bytes
    upload.file.seek(0)
    data = upload.file.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise ServiceError(f"Image is larger than {settings.max_image_size_mb} MB.", 413)
    if not data:
        raise ServiceError("The cover image is empty.", 400)
    return data
