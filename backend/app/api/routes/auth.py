from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Request, Response, status

from app.api.deps import CurrentUser, DbSession
from app.core.ratelimit import login_throttle
from app.core.security import (
    DUMMY_HASH,
    create_access_token,
    hash_password,
    verify_password,
)
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import PasswordChange, UserOut
from app.services.users import get_by_username

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: DbSession) -> TokenResponse:
    username = payload.username.strip().lower()
    ip = request.client.host if request.client else "unknown"
    throttle_key = f"{ip}:{username}"
    login_throttle.check(throttle_key)

    user = get_by_username(db, username)
    password_ok = verify_password(payload.password, user.password_hash if user else DUMMY_HASH)
    if user is None or not password_ok or not user.is_active:
        login_throttle.fail(throttle_key)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect username or password.")

    login_throttle.reset(throttle_key)
    user.last_login_at = datetime.now(UTC)
    db.commit()
    token, expires_at = create_access_token(user.id)
    return TokenResponse(access_token=token, expires_at=expires_at, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser) -> UserOut:
    return UserOut.model_validate(user)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(payload: PasswordChange, user: CurrentUser, db: DbSession) -> Response:
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Current password is incorrect.")
    user.password_hash = hash_password(payload.new_password)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
