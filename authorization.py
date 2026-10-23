from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from database import get_db
from models import User

def can_read_document(user, document, permission=None) -> bool:
    if user is None or not user.is_active:
        return False

    if document.owner_id == user.id:
        return True

    if permission is None:
        return False

    return permission.can_read or permission.can_edit


def can_edit_document(user, document, permission=None) -> bool:
    if user is None or not user.is_active:
        return False

    if document.owner_id == user.id:
        return True

    return permission is not None and permission.can_edit


def can_delete_document(user, document) -> bool:
    if user is None or not user.is_active:
        return False

    return document.owner_id == user.id


def can_manage_sharing(user, document) -> bool:
    if user is None or not user.is_active:
        return False

    return document.owner_id == user.id

def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    user_id = request.session.get("user_id")

    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Please log in",
        )

    user = db.get(User, user_id)

    if user is None or not user.is_active:
        request.session.clear()
        raise HTTPException(
            status_code=401,
            detail="Please log in",
        )

    return user