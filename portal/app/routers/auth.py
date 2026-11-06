from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import current_user
from app.schemas import RegisterForm, parse
from app.services import UserService
from app.templating import render

router = APIRouter()


@router.get("/register")
def register_page(request: Request, user=Depends(current_user)):
    return render(request, "register.html", user, errors={}, values={})


@router.post("/register")
def register(
    request: Request,
    login: str = Form(""),
    email: str = Form(""),
    phone: str = Form(""),
    password: str = Form(""),
    password2: str = Form(""),
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    data = dict(login=login, email=email, phone=phone, password=password, password2=password2)
    form, errors = parse(RegisterForm, data)
    service = UserService(db)
    if form and service.by_login(form.login):
        errors["login"] = "Такой логин уже занят"
    if errors:
        return render(request, "register.html", user, status_code=422, errors=errors, values=data)
    new_user = service.register(form)
    request.session["user_id"] = new_user.id
    request.session["flash"] = "Регистрация прошла, вы вошли в аккаунт"
    return RedirectResponse("/", status_code=303)


@router.get("/login")
def login_page(request: Request, next: str = "/", user=Depends(current_user)):
    return render(request, "login.html", user, errors={}, values={}, next=next)


@router.post("/login")
def login(
    request: Request,
    login: str = Form(""),
    password: str = Form(""),
    next: str = Form("/"),
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    found = UserService(db).authenticate(login, password)
    if not found:
        errors = {"form": "Неверный логин или пароль"}
        return render(request, "login.html", user, status_code=401, errors=errors, values={"login": login}, next=next)
    request.session["user_id"] = found.id
    target = next if next.startswith("/") and not next.startswith("//") else "/"
    return RedirectResponse(target, status_code=303)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)
