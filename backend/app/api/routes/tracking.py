from fastapi import APIRouter, Request, Response, status
from pydantic import BaseModel, Field

from app.api.deps import DbSession
from app.models import Newsletter, Visit
from app.services.visitors import (
    client_fingerprint,
    get_or_create_visitor_id,
    is_bot,
    set_visitor_cookie,
)

router = APIRouter(prefix="/track", tags=["tracking"])


class VisitIn(BaseModel):
    path: str = Field(max_length=300)
    newsletter_id: int | None = None


@router.post("/visit", status_code=status.HTTP_204_NO_CONTENT)
def track_visit(payload: VisitIn, request: Request, db: DbSession) -> Response:
    """Called by the public pages on load. Sets/refreshes the anonymous visitor cookie."""
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    visitor_id = get_or_create_visitor_id(request)
    set_visitor_cookie(response, visitor_id)

    user_agent, ip_hash = client_fingerprint(request)
    if is_bot(user_agent):
        return response

    newsletter_id = payload.newsletter_id
    if newsletter_id is not None and db.get(Newsletter, newsletter_id) is None:
        newsletter_id = None

    db.add(
        Visit(
            visitor_id=visitor_id,
            path=payload.path,
            newsletter_id=newsletter_id,
            user_agent=user_agent,
            ip_hash=ip_hash,
        )
    )
    db.commit()
    return response
