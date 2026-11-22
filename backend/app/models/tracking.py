from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Visit(Base):
    """One public page view. Anonymous: identified only by a random first-party cookie id."""

    __tablename__ = "visits"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    visitor_id: Mapped[str] = mapped_column(String(32), index=True)
    path: Mapped[str] = mapped_column(String(300))
    newsletter_id: Mapped[int | None] = mapped_column(
        ForeignKey("newsletters.id", ondelete="CASCADE"), index=True, default=None
    )
    user_agent: Mapped[str] = mapped_column(String(300), default="")
    ip_address: Mapped[str] = mapped_column(String(45), default="")  # IPv4 or IPv6
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)


class Download(Base):
    __tablename__ = "downloads"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    newsletter_id: Mapped[int] = mapped_column(
        ForeignKey("newsletters.id", ondelete="CASCADE"), index=True
    )
    visitor_id: Mapped[str] = mapped_column(String(32), index=True)
    user_agent: Mapped[str] = mapped_column(String(300), default="")
    ip_address: Mapped[str] = mapped_column(String(45), default="")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)
