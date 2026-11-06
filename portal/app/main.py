from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.config import BASE_DIR, settings
from app.deps import CsrfError, Forbidden, NeedLogin, user_from_request
from app.routers import admin, applications, auth, pages
from app.templating import render

app = FastAPI(title="Конференции.РФ")
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    session_cookie="konf_session",
    max_age=settings.session_hours * 3600,
    same_site="lax",
    https_only=settings.https_only,
)
app.mount("/static", StaticFiles(directory=BASE_DIR / "app" / "static"), name="static")

app.include_router(pages.router)
app.include_router(auth.router)
app.include_router(applications.router)
app.include_router(admin.router)


@app.exception_handler(NeedLogin)
def need_login(request: Request, exc: NeedLogin):
    return RedirectResponse("/login?next=" + request.url.path, status_code=303)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "same-origin"
    return response


@app.exception_handler(CsrfError)
def csrf_error(request: Request, exc: CsrfError):
    return render(request, "error.html", user_from_request(request), status_code=403, code=403, text="Форма устарела. Откройте страницу заново и повторите действие")


@app.exception_handler(Forbidden)
def forbidden(request: Request, exc: Forbidden):
    return render(request, "error.html", user_from_request(request), status_code=403, code=403, text="Эта страница только для администратора")


ERROR_TEXTS = {
    400: "Некорректный запрос",
    404: "Страница не найдена",
    405: "Так открывать этот адрес нельзя",
}


@app.exception_handler(HTTPException)
def http_error(request: Request, exc: HTTPException):
    text = ERROR_TEXTS.get(exc.status_code, "Ошибка")
    return render(request, "error.html", user_from_request(request), status_code=exc.status_code, code=exc.status_code, text=text)


@app.exception_handler(RequestValidationError)
def bad_request(request: Request, exc: RequestValidationError):
    # неверный номер в адресе (буквы, ноль, слишком большое число) для человека то же самое, что нет такой страницы
    return render(request, "error.html", user_from_request(request), status_code=404, code=404, text=ERROR_TEXTS[404])
