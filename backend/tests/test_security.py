from datetime import UTC, datetime, timedelta

import jwt

from app.core.config import settings
from app.core.security import (
    ALGORITHM,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_roundtrip_including_long_and_unicode():
    for pw in ("correct horse", "x" * 200, "كلمة-سر-طويلة-جدا"):
        hashed = hash_password(pw)
        assert verify_password(pw, hashed)
        assert not verify_password(pw + "!", hashed)


def test_token_lifetime_is_eight_hours_by_default():
    assert settings.access_token_expire_minutes == 480
    token, expires_at = create_access_token(42)
    remaining = expires_at - datetime.now(UTC)
    assert timedelta(hours=7, minutes=59) < remaining <= timedelta(hours=8)
    assert decode_access_token(token) == 42


def test_expired_and_tampered_tokens_are_rejected():
    expired = jwt.encode(
        {"sub": "1", "exp": datetime.now(UTC) - timedelta(seconds=1)},
        settings.secret_key,
        algorithm=ALGORITHM,
    )
    assert decode_access_token(expired) is None

    token, _ = create_access_token(1)
    assert decode_access_token(token + "x") is None
    forged = jwt.encode(
        {"sub": "1", "exp": datetime.now(UTC) + timedelta(hours=1)}, "wrong-key" * 5, algorithm=ALGORITHM
    )
    assert decode_access_token(forged) is None
