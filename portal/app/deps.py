from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User


class NeedLogin(Exception):
    pass


class Forbidden(Exception):
    pass


def current_user(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.get(User, user_id)


def login_required(user=Depends(current_user)):
    if user is None:
        raise NeedLogin()
    return user


def admin_required(user=Depends(login_required)):
    if user.role != "admin":
        raise Forbidden()
    return user
