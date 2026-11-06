import re

from pydantic import BaseModel, ValidationError, field_validator

LOGIN_RE = re.compile(r"^[A-Za-z0-9_]{3,30}$")
EMAIL_RE = re.compile(r"^[\w.+-]+@[\w-]+(\.[\w-]+)+$")
PHONE_RE = re.compile(r"^(\+7|8)[\s(-]*\d{3}[\s)-]*\d{3}[\s-]*\d{2}[\s-]*\d{2}$")


def parse(model, data):
    """Проверяет данные формы. Возвращает (объект, {поле: текст ошибки})."""
    try:
        return model(**data), {}
    except ValidationError as e:
        errors = {}
        for err in e.errors():
            field = err["loc"][0] if err["loc"] else "form"
            ctx = err.get("ctx") or {}
            errors.setdefault(field, str(ctx.get("error", err["msg"])))
        return None, errors


class RegisterForm(BaseModel):
    login: str
    email: str
    phone: str
    password: str
    password2: str

    @field_validator("login")
    @classmethod
    def check_login(cls, v):
        if not LOGIN_RE.match(v):
            raise ValueError("Логин: от 3 до 30 символов, латинские буквы, цифры и знак _")
        return v

    @field_validator("email")
    @classmethod
    def check_email(cls, v):
        if not EMAIL_RE.match(v):
            raise ValueError("Почта указана неверно, пример: anna@mail.ru")
        return v

    @field_validator("phone")
    @classmethod
    def check_phone(cls, v):
        if not PHONE_RE.match(v):
            raise ValueError("Телефон в формате +7 916 123-45-67 или 8 916 123-45-67")
        digits = re.sub(r"\D", "", v)
        return "+7" + digits[-10:]

    @field_validator("password")
    @classmethod
    def check_password(cls, v):
        if len(v) < 8:
            raise ValueError("Пароль: не короче 8 символов")
        return v

    @field_validator("password2")
    @classmethod
    def check_password2(cls, v, info):
        if v != info.data.get("password"):
            raise ValueError("Пароли не совпадают")
        return v


class ApplicationForm(BaseModel):
    room: str
    payment: str
    comment: str = ""

    @field_validator("room")
    @classmethod
    def check_room(cls, v):
        if not v.strip():
            raise ValueError("Укажите помещение")
        if len(v) > 60:
            raise ValueError("Помещение: не больше 60 символов")
        return v.strip()

    @field_validator("payment")
    @classmethod
    def check_payment(cls, v):
        if not v.strip():
            raise ValueError("Укажите способ оплаты")
        if len(v) > 40:
            raise ValueError("Способ оплаты: не больше 40 символов")
        return v.strip()

    @field_validator("comment")
    @classmethod
    def check_comment(cls, v):
        if len(v) > 300:
            raise ValueError("Комментарий: не больше 300 символов")
        return v.strip()
