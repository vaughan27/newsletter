import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.user import Role

_USERNAME_RE = re.compile(r"^[a-z0-9._-]{3,64}$")


def _normalize_username(v: str) -> str:
    v = v.strip().lower()
    if not _USERNAME_RE.fullmatch(v):
        raise ValueError("Username must be 3-64 characters: letters, numbers, dot, dash, underscore.")
    return v


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    full_name: str
    role: Role
    is_active: bool
    created_at: datetime
    last_login_at: datetime | None


class UserCreate(BaseModel):
    username: str
    full_name: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=8, max_length=128)
    role: Role = Role.MANAGER
    is_active: bool = True

    _check_username = field_validator("username")(_normalize_username)


class UserUpdate(BaseModel):
    username: str | None = None
    full_name: str | None = Field(default=None, min_length=1, max_length=120)
    password: str | None = Field(default=None, min_length=8, max_length=128)
    role: Role | None = None
    is_active: bool | None = None

    @field_validator("username")
    @classmethod
    def _check_username(cls, v: str | None) -> str | None:
        return None if v is None else _normalize_username(v)


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)
