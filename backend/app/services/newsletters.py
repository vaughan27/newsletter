import re
import uuid
from datetime import date
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.errors import ServiceError
from app.models import Newsletter, User
from app.services import covers, storage


def download_name(title: str) -> str:
    slug = re.sub(r"[^\w\-]+", "-", title, flags=re.UNICODE).strip("-")
    return f"{slug or 'newsletter'}.pdf"


def create_newsletter(
    db: Session,
    *,
    user: User,
    pdf: UploadFile,
    title: str,
    publication_date: date,
    description: str,
    cover_mode: str,
    cover_image: UploadFile | None,
) -> Newsletter:
    uid = uuid.uuid4().hex
    pdf_file = storage.pdf_path(f"{uid}.pdf")
    cover_file = storage.cover_path(f"{uid}.jpg")

    if cover_mode == "custom" and cover_image is None:
        raise ServiceError("Choose a cover image, or use the first slide of the PDF.", 400)

    try:
        size = storage.save_pdf_upload(pdf, pdf_file)
        page_count = covers.validate_pdf(pdf_file)
        if cover_mode == "custom":
            assert cover_image is not None
            covers.write_cover_from_image(storage.read_image_upload(cover_image), cover_file)
        else:
            covers.write_cover_from_pdf(pdf_file, cover_file)

        newsletter = Newsletter(
            title=title.strip(),
            description=description.strip(),
            publication_date=publication_date,
            pdf_filename=pdf_file.name,
            cover_filename=cover_file.name,
            cover_source="custom" if cover_mode == "custom" else "slide",
            pdf_size_bytes=size,
            page_count=page_count,
            uploaded_by_id=user.id,
        )
        db.add(newsletter)
        db.commit()
    except BaseException:
        db.rollback()
        storage.safe_delete(pdf_file, cover_file)
        raise
    db.refresh(newsletter)
    return newsletter


def update_newsletter(
    db: Session,
    newsletter: Newsletter,
    *,
    title: str | None,
    publication_date: date | None,
    description: str | None,
    cover_mode: str,  # "keep" | "slide" | "custom"
    cover_image: UploadFile | None,
    pdf: UploadFile | None,
) -> Newsletter:
    if cover_mode == "custom" and cover_image is None:
        raise ServiceError("Choose a cover image to upload.", 400)

    old_files: list[Path] = []
    new_files: list[Path] = []
    try:
        pdf_name = newsletter.pdf_filename
        if pdf is not None:
            uid = uuid.uuid4().hex
            new_pdf = storage.pdf_path(f"{uid}.pdf")
            new_files.append(new_pdf)
            newsletter.pdf_size_bytes = storage.save_pdf_upload(pdf, new_pdf)
            newsletter.page_count = covers.validate_pdf(new_pdf)
            old_files.append(storage.pdf_path(newsletter.pdf_filename))
            pdf_name = new_pdf.name
            newsletter.pdf_filename = pdf_name

        # A replaced PDF with a slide-based cover gets a fresh slide cover automatically.
        effective_mode = cover_mode
        if cover_mode == "keep" and pdf is not None and newsletter.cover_source == "slide":
            effective_mode = "slide"

        if effective_mode in ("slide", "custom"):
            new_cover = storage.cover_path(f"{uuid.uuid4().hex}.jpg")
            new_files.append(new_cover)
            if effective_mode == "custom":
                assert cover_image is not None
                covers.write_cover_from_image(storage.read_image_upload(cover_image), new_cover)
            else:
                covers.write_cover_from_pdf(storage.pdf_path(pdf_name), new_cover)
            old_files.append(storage.cover_path(newsletter.cover_filename))
            newsletter.cover_filename = new_cover.name
            newsletter.cover_source = effective_mode

        if title is not None:
            newsletter.title = title.strip()
        if publication_date is not None:
            newsletter.publication_date = publication_date
        if description is not None:
            newsletter.description = description.strip()

        db.commit()
    except BaseException:
        db.rollback()
        storage.safe_delete(*new_files)
        raise

    storage.safe_delete(*old_files)
    db.refresh(newsletter)
    return newsletter


def delete_newsletter(db: Session, newsletter: Newsletter) -> None:
    pdf_file = storage.pdf_path(newsletter.pdf_filename)
    cover_file = storage.cover_path(newsletter.cover_filename)
    db.delete(newsletter)
    db.commit()
    storage.safe_delete(pdf_file, cover_file)
