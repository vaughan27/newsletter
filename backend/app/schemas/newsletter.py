import os

from dotenv import load_dotenv

from datetime import date, datetime

from pydantic import BaseModel

from app.models.newsletter import Newsletter

load_dotenv()
API_PUBLIC_PREFIX = os.getenv("API_PUBLIC_PREFIX", "/api").rstrip("/")

class NewsletterOut(BaseModel):
    id: int
    title: str
    description: str
    publication_date: date
    cover_url: str
    pdf_url: str
    download_url: str
    cover_source: str
    page_count: int
    pdf_size_bytes: int
    created_at: datetime
    updated_at: datetime


def to_out(n: Newsletter) -> NewsletterOut:
    # The ?v= stamp changes whenever the row is updated, so covers can be cached "forever".
    version = int(n.updated_at.timestamp())
    return NewsletterOut(
        id=n.id,
        title=n.title,
        description=n.description,
        publication_date=n.publication_date,
        cover_url=f"{API_PUBLIC_PREFIX}/newsletters/{n.id}/cover?v={version}",
        pdf_url=f"{API_PUBLIC_PREFIX}/newsletters/{n.id}/pdf",
        download_url=f"{API_PUBLIC_PREFIX}/newsletters/{n.id}/download",
        cover_source=n.cover_source,
        page_count=n.page_count,
        pdf_size_bytes=n.pdf_size_bytes,
        created_at=n.created_at,
        updated_at=n.updated_at,
    )
