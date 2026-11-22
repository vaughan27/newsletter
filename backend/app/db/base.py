from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    # Every datetime column is timezone-aware (stored as UTC by Postgres).
    type_annotation_map = {datetime: DateTime(timezone=True)}
