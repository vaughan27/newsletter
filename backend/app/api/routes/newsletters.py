from datetime import date
from typing import Literal

from fastapi import APIRouter, File, Form, HTTPException, Request, Response, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select

from app.api.deps import AdminUser, DbSession, StaffUser
from app.models import Download, Newsletter
from app.schemas.newsletter import NewsletterOut, to_out
from app.services import newsletters as service
from app.services import storage
from app.services.visitors import (
    client_fingerprint,
    get_or_create_visitor_id,
    is_bot,
    set_visitor_cookie,
)

router = APIRouter(prefix="/newsletters", tags=["newsletters"])


def _get_or_404(db: DbSession, newsletter_id: int) -> Newsletter:
    newsletter = db.get(Newsletter, newsletter_id)
    if newsletter is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Newsletter not found.")
    return newsletter


# ---------- public (no login) ----------


@router.get("", response_model=list[NewsletterOut])
def list_newsletters(db: DbSession):
    rows = db.scalars(
        select(Newsletter).order_by(Newsletter.publication_date.desc(), Newsletter.id.desc())
    ).all()
    return [to_out(n) for n in rows]


@router.get("/{newsletter_id}", response_model=NewsletterOut)
def get_newsletter(newsletter_id: int, db: DbSession):
    return to_out(_get_or_404(db, newsletter_id))


@router.get("/{newsletter_id}/cover")
def get_cover(newsletter_id: int, db: DbSession):
    newsletter = _get_or_404(db, newsletter_id)
    path = storage.cover_path(newsletter.cover_filename)
    if not path.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cover not found.")
    # URLs carry ?v=<updated_at>, so a changed cover always gets a new URL.
    return FileResponse(
        path,
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
    )


@router.get("/{newsletter_id}/pdf")
def view_pdf(newsletter_id: int, db: DbSession):
    """Inline PDF for the on-page viewer. Not counted as a download."""
    newsletter = _get_or_404(db, newsletter_id)
    path = storage.pdf_path(newsletter.pdf_filename)
    if not path.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "PDF not found.")
    return FileResponse(
        path,
        media_type="application/pdf",
        filename=service.download_name(newsletter.title),
        content_disposition_type="inline",
    )


@router.get("/{newsletter_id}/download")
def download_pdf(newsletter_id: int, request: Request, db: DbSession):
    newsletter = _get_or_404(db, newsletter_id)
    path = storage.pdf_path(newsletter.pdf_filename)
    if not path.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "PDF not found.")

    visitor_id = get_or_create_visitor_id(request)
    user_agent, ip_hash = client_fingerprint(request)
    if not is_bot(user_agent):
        db.add(
            Download(
                newsletter_id=newsletter.id,
                visitor_id=visitor_id,
                user_agent=user_agent,
                ip_hash=ip_hash,
            )
        )
        db.commit()

    response = FileResponse(
        path,
        media_type="application/pdf",
        filename=service.download_name(newsletter.title),
        content_disposition_type="attachment",
    )
    set_visitor_cookie(response, visitor_id)
    return response


# ---------- staff: admin + manager ----------


@router.post("", response_model=NewsletterOut, status_code=status.HTTP_201_CREATED)
def upload_newsletter(
    user: StaffUser,
    db: DbSession,
    pdf: UploadFile = File(...),
    title: str = Form(..., min_length=1, max_length=200),
    publication_date: date = Form(...),
    description: str = Form("", max_length=5000),
    cover_mode: Literal["slide", "custom"] = Form("slide"),
    cover_image: UploadFile | None = File(None),
):
    newsletter = service.create_newsletter(
        db,
        user=user,
        pdf=pdf,
        title=title,
        publication_date=publication_date,
        description=description,
        cover_mode=cover_mode,
        cover_image=cover_image,
    )
    return to_out(newsletter)


# ---------- admin only ----------


@router.patch("/{newsletter_id}", response_model=NewsletterOut)
def update_newsletter(
    newsletter_id: int,
    _: AdminUser,
    db: DbSession,
    title: str | None = Form(None, min_length=1, max_length=200),
    publication_date: date | None = Form(None),
    description: str | None = Form(None, max_length=5000),
    cover_mode: Literal["keep", "slide", "custom"] = Form("keep"),
    cover_image: UploadFile | None = File(None),
    pdf: UploadFile | None = File(None),
):
    newsletter = service.update_newsletter(
        db,
        _get_or_404(db, newsletter_id),
        title=title,
        publication_date=publication_date,
        description=description,
        cover_mode=cover_mode,
        cover_image=cover_image,
        pdf=pdf,
    )
    return to_out(newsletter)


@router.delete("/{newsletter_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_newsletter(newsletter_id: int, _: AdminUser, db: DbSession) -> Response:
    service.delete_newsletter(db, _get_or_404(db, newsletter_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
