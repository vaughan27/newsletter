"""Anonymous visitor identification.

Normal users never log in. We give each browser a random, first-party, HttpOnly cookie
(`visitor_id`, 1 year). Unique visitors are counted by distinct cookie id. The client IP
address is stored with each visit/download; the cookie id itself isn't linked to a person.
"""

import re
import uuid

from fastapi import Request, Response

from app.core.config import settings

VISITOR_COOKIE = "visitor_id"
_COOKIE_MAX_AGE = 365 * 24 * 60 * 60
_VALID_ID = re.compile(r"^[0-9a-f]{32}$")
_BOT_RE = re.compile(
    r"bot|crawl|spider|slurp|headless|preview|monitor|curl|wget|python-requests|httpx|scanner",
    re.IGNORECASE,
)


def is_bot(user_agent: str) -> bool:
    return not user_agent or bool(_BOT_RE.search(user_agent))


def get_or_create_visitor_id(request: Request) -> str:
    existing = request.cookies.get(VISITOR_COOKIE, "")
    return existing if _VALID_ID.fullmatch(existing) else uuid.uuid4().hex


def set_visitor_cookie(response: Response, visitor_id: str) -> None:
    response.set_cookie(
        VISITOR_COOKIE,
        visitor_id,
        max_age=_COOKIE_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        path="/",
    )


def client_fingerprint(request: Request) -> tuple[str, str]:
    """(user_agent, client ip address)"""
    user_agent = request.headers.get("user-agent", "")[:300]
    ip = request.client.host if request.client else ""
    return user_agent, ip[:45]
