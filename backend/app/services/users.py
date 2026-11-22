import logging

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import ServiceError
from app.core.security import hash_password
from app.models import Role, User
from app.schemas.user import UserCreate, UserUpdate

log = logging.getLogger(__name__)


def get_by_username(db: Session, username: str) -> User | None:
    return db.scalar(select(User).where(User.username == username))


def _other_active_admins(db: Session, exclude_id: int) -> int:
    return (
        db.scalar(
            select(func.count(User.id)).where(
                User.role == Role.ADMIN.value, User.is_active.is_(True), User.id != exclude_id
            )
        )
        or 0
    )


def create_user(db: Session, data: UserCreate) -> User:
    if get_by_username(db, data.username):
        raise ServiceError("That username is already taken.", 409)
    user = User(
        username=data.username,
        full_name=data.full_name.strip(),
        password_hash=hash_password(data.password),
        role=data.role.value,
        is_active=data.is_active,
    )
    db.add(user)
    db.commit()
    return user


def update_user(db: Session, user: User, data: UserUpdate, *, acting: User) -> User:
    new_role = data.role.value if data.role is not None else user.role
    new_active = data.is_active if data.is_active is not None else user.is_active

    if user.id == acting.id and (new_role != user.role or not new_active):
        raise ServiceError("You can't change your own role or deactivate your own account.", 400)
    was_admin = user.role == Role.ADMIN.value and user.is_active
    stays_admin = new_role == Role.ADMIN.value and new_active
    if was_admin and not stays_admin and _other_active_admins(db, user.id) == 0:
        raise ServiceError("There must be at least one active admin.", 400)

    if data.username is not None and data.username != user.username:
        if get_by_username(db, data.username):
            raise ServiceError("That username is already taken.", 409)
        user.username = data.username
    if data.full_name is not None:
        user.full_name = data.full_name.strip()
    if data.password is not None:
        user.password_hash = hash_password(data.password)
    user.role = new_role
    user.is_active = new_active
    db.commit()
    return user


def delete_user(db: Session, user: User, *, acting: User) -> None:
    if user.id == acting.id:
        raise ServiceError("You can't delete your own account.", 400)
    if (
        user.role == Role.ADMIN.value
        and user.is_active
        and _other_active_admins(db, user.id) == 0
    ):
        raise ServiceError("There must be at least one active admin.", 400)
    db.delete(user)
    db.commit()


def ensure_first_admin(db: Session) -> None:
    """Bootstrap the first admin from env vars when the users table is empty."""
    if (db.scalar(select(func.count(User.id))) or 0) > 0:
        return
    if not settings.first_admin_password:
        log.warning(
            "No users exist and FIRST_ADMIN_PASSWORD is not set: nobody can log in. "
            "Set it in backend/.env and restart."
        )
        return
    db.add(
        User(
            username=settings.first_admin_username.strip().lower(),
            full_name=settings.first_admin_full_name,
            password_hash=hash_password(settings.first_admin_password),
            role=Role.ADMIN.value,
        )
    )
    db.commit()
    log.info("Created first admin user '%s'.", settings.first_admin_username)
