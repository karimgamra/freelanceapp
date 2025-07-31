from fastapi import status, HTTPException
from uuid import UUID

from app.utils.exceptions import raise_forbidden
from ..models.user import User
from sqlalchemy.orm import Session


def validate_uuid(id: str) -> UUID:
    try:
        return UUID(id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")


def get_user_by_id(user: User, db: Session) -> User:
    db_user = db.query(User).filter(User.id == user.id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User Not Found")
    return db_user


def ensure_not_admin(user: User):
    if user.role == "admin":
        raise HTTPException(
            status_code=403, detail="Admin cannot be modified like this"
        )


def ensure_client(user):
    if not user or user.role != "client":
        raise_forbidden("Only clients can perform this action")
