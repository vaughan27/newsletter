import base64
import hashlib
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from app.core.config import settings

ALGORITHM = "HS256"


def _prepare(password: str) -> bytes:
    # bcrypt only reads the first 72 bytes (and newer versions reject longer input).
    # Pre-hashing keeps long passphrases and non-ASCII input safe.
    return base64.b64encode(hashlib.sha256(password.encode("utf-8")).digest())


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_prepare(password), bcrypt.gensalt()).decode("ascii")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(_prepare(password), password_hash.encode("ascii"))
    except ValueError:
        return False


# Used to spend the same time on unknown usernames as on real ones.
DUMMY_HASH = hash_password("not-a-real-password")


def create_access_token(user_id: int) -> tuple[str, datetime]:
    now = datetime.now(UTC)
    expires_at = now + timedelta(minutes=settings.access_token_expire_minutes)
    token = jwt.encode(
        {"sub": str(user_id), "iat": now, "exp": expires_at},
        settings.secret_key,
        algorithm=ALGORITHM,
    )
    return token, expires_at


def decode_access_token(token: str) -> int | None:
    """Return the user id for a valid, unexpired token, else None."""
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[ALGORITHM], options={"require": ["exp", "sub"]}
        )
        return int(payload["sub"])
    except (jwt.PyJWTError, ValueError, KeyError):
        return None
