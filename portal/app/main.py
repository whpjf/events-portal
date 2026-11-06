from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.config import BASE_DIR, settings
from app.deps import Forbidden, NeedLogin
from app.routers import admin, applications, auth, pages
from app.templating import render

app = FastAPI(title="Конференции.РФ")
app.add_middleware(SessionMiddleware, secret_key=settings.secret_key, max_age=settings.session_hours * 3600)
app.mount("/static", StaticFiles(directory=BASE_DIR / "app" / "static"), name="static")

app.include_router(pages.router)
app.include_router(auth.router)
app.include_router(applications.router)
app.include_router(admin.router)


@app.exception_handler(NeedLogin)
def need_login(request: Request, exc: NeedLogin):
    return RedirectResponse("/login?next=" + request.url.path, status_code=303)


@app.exception_handler(Forbidden)
def forbidden(request: Request, exc: Forbidden):
    return render(request, "error.html", None, status_code=403, code=403, text="Эта страница только для администратора")


@app.exception_handler(HTTPException)
def http_error(request: Request, exc: HTTPException):
    texts = {404: "Страница не найдена"}
    return render(request, "error.html", None, status_code=exc.status_code, code=exc.status_code, text=texts.get(exc.status_code, "Ошибка"))
