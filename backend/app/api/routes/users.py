from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import select

from app.api.deps import AdminUser, DbSession
from app.models import User
from app.schemas.user import UserCreate, UserOut, UserUpdate
from app.services import users as user_service

router = APIRouter(prefix="/users", tags=["users"])


def _get_or_404(db: DbSession, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found.")
    return user


@router.get("", response_model=list[UserOut])
def list_users(_: AdminUser, db: DbSession):
    return db.scalars(select(User).order_by(User.username)).all()


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, _: AdminUser, db: DbSession):
    return user_service.create_user(db, payload)


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, _: AdminUser, db: DbSession):
    return _get_or_404(db, user_id)


@router.patch("/{user_id}", response_model=UserOut)
def update_user(user_id: int, payload: UserUpdate, acting: AdminUser, db: DbSession):
    return user_service.update_user(db, _get_or_404(db, user_id), payload, acting=acting)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, acting: AdminUser, db: DbSession) -> Response:
    user_service.delete_user(db, _get_or_404(db, user_id), acting=acting)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
