from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import current_user
from app.schemas import RegisterForm, parse
from app.security import guard, verify_csrf
from app.services import UserService
from app.templating import render

router = APIRouter()


@router.get("/register")
def register_page(request: Request, user=Depends(current_user)):
    return render(request, "register.html", user, errors={}, values={})


@router.post("/register", dependencies=[Depends(verify_csrf)])
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
    request.session.clear()
    request.session["user_id"] = new_user.id
    request.session["flash"] = "Регистрация прошла, вы вошли в аккаунт"
    return RedirectResponse("/", status_code=303)


@router.get("/login")
def login_page(request: Request, next: str = "/", user=Depends(current_user)):
    return render(request, "login.html", user, errors={}, values={}, next=next)


@router.post("/login", dependencies=[Depends(verify_csrf)])
def login(
    request: Request,
    login: str = Form(""),
    password: str = Form(""),
    next: str = Form("/"),
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    key = f"{login.lower()}|{request.client.host}"
    left = guard.seconds_left(key)
    if left:
        errors = {"form": f"Слишком много неудачных попыток. Подождите {left // 60 + 1} мин. и попробуйте снова"}
        return render(request, "login.html", user, status_code=429, errors=errors, values={"login": login}, next=next)
    found = UserService(db).authenticate(login, password)
    if not found:
        guard.fail(key)
        errors = {"form": "Неверный логин или пароль"}
        return render(request, "login.html", user, status_code=401, errors=errors, values={"login": login}, next=next)
    guard.ok(key)
    request.session.clear()
    request.session["user_id"] = found.id
    target = next if next.startswith("/") and not next.startswith("//") else "/"
    return RedirectResponse(target, status_code=303)


@router.post("/logout", dependencies=[Depends(verify_csrf)])
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)
