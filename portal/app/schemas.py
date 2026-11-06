import re

from pydantic import BaseModel, ValidationError, field_validator

from datetime import datetime

from app.choices import IMAGES, PAYMENTS, ROOMS

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
        if v not in ROOMS:
            raise ValueError("Выберите помещение из списка")
        return v

    @field_validator("payment")
    @classmethod
    def check_payment(cls, v):
        if v not in PAYMENTS:
            raise ValueError("Выберите способ оплаты из списка")
        return v

    @field_validator("comment")
    @classmethod
    def check_comment(cls, v):
        if len(v) > 300:
            raise ValueError("Комментарий: не больше 300 символов")
        return v.strip()


class ReviewForm(BaseModel):
    rating: int
    body: str

    @field_validator("rating", mode="before")
    @classmethod
    def check_rating(cls, v):
        try:
            v = int(v)
        except (TypeError, ValueError):
            raise ValueError("Поставьте оценку от 1 до 5")
        if not 1 <= v <= 5:
            raise ValueError("Оценка от 1 до 5")
        return v

    @field_validator("body")
    @classmethod
    def check_body(cls, v):
        v = v.strip()
        if len(v) < 5:
            raise ValueError("Отзыв: не короче 5 символов")
        if len(v) > 500:
            raise ValueError("Отзыв: не длиннее 500 символов")
        return v


class EventForm(BaseModel):
    title: str
    event_date: datetime
    place: str
    description: str
    image: str

    @field_validator("title")
    @classmethod
    def check_title(cls, v):
        v = v.strip()
        if not 3 <= len(v) <= 120:
            raise ValueError("Название: от 3 до 120 символов")
        return v

    @field_validator("event_date", mode="before")
    @classmethod
    def check_date(cls, v):
        try:
            return datetime.fromisoformat(v)
        except (TypeError, ValueError):
            raise ValueError("Укажите дату и время мероприятия")

    @field_validator("place")
    @classmethod
    def check_place(cls, v):
        v = v.strip()
        if not 3 <= len(v) <= 120:
            raise ValueError("Место: от 3 до 120 символов")
        return v

    @field_validator("description")
    @classmethod
    def check_description(cls, v):
        v = v.strip()
        if not 10 <= len(v) <= 2000:
            raise ValueError("Описание: от 10 до 2000 символов")
        return v

    @field_validator("image")
    @classmethod
    def check_image(cls, v):
        if v not in IMAGES:
            raise ValueError("Выберите фото из списка")
        return v
