from typing import Annotated

from fastapi import Depends, Path, Request
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db
from app.models import User


# номер записи в адресе: целое от 1 до 2147483647, иначе сразу страница «не найдено»
RecordId = Annotated[int, Path(ge=1, le=2**31 - 1)]


class NeedLogin(Exception):
    pass


class Forbidden(Exception):
    pass


class CsrfError(Exception):
    pass


def current_user(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.get(User, user_id)


def user_from_request(request: Request):
    """Для страниц ошибок: вошедший человек остаётся вошедшим и в шапке."""
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    db = SessionLocal()
    try:
        user = db.get(User, user_id)
        if user:
            db.expunge(user)
        return user
    finally:
        db.close()


def login_required(user=Depends(current_user)):
    if user is None:
        raise NeedLogin()
    return user


def admin_required(user=Depends(login_required)):
    if user.role != "admin":
        raise Forbidden()
    return user
