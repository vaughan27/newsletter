import re
from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_DIR = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/newsletters"
    secret_key: str = Field(min_length=32)
    access_token_expire_minutes: int = 480

    first_admin_username: str = "admin"
    first_admin_password: str | None = None
    first_admin_full_name: str = "Administrator"

    app_timezone: str = "Asia/Kuwait"
    cookie_secure: bool = False
    cors_origins: str = ""

    storage_dir: Path = BACKEND_DIR / "storage"
    frontend_dist: Path = PROJECT_DIR / "frontend" / "dist"

    max_pdf_size_mb: int = 50
    max_image_size_mb: int = 10

    cover_aspect_width: int = 16
    cover_aspect_height: int = 9
    cover_width_px: int = 1280

    @field_validator("app_timezone")
    @classmethod
    def _valid_timezone(cls, v: str) -> str:
        # Also interpolated into SQL as a literal, so keep it strictly charset-limited.
        if not re.fullmatch(r"[A-Za-z0-9_+\-/]+", v):
            raise ValueError("Invalid timezone name")
        ZoneInfo(v)
        return v

    @property
    def max_pdf_bytes(self) -> int:
        return self.max_pdf_size_mb * 1024 * 1024

    @property
    def max_image_bytes(self) -> int:
        return self.max_image_size_mb * 1024 * 1024

    @property
    def cover_size(self) -> tuple[int, int]:
        height = round(self.cover_width_px * self.cover_aspect_height / self.cover_aspect_width)
        return self.cover_width_px, height

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def pdf_dir(self) -> Path:
        return self.storage_dir / "pdfs"

    @property
    def cover_dir(self) -> Path:
        return self.storage_dir / "covers"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
