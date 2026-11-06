from datetime import datetime

from fastapi.templating import Jinja2Templates

from app.config import BASE_DIR
from app.security import get_csrf
from app.services import STATUS_LABELS

templates = Jinja2Templates(directory=str(BASE_DIR / "app" / "templates"))
templates.env.filters["status_label"] = lambda s: STATUS_LABELS.get(s, s)
templates.env.filters["date_ru"] = lambda d: d.strftime("%d.%m.%Y %H:%M")


def render(request, name, user=None, status_code=200, **ctx):
    flash = request.session.pop("flash", None)
    ctx.update(user=user, flash=flash, now=datetime.now(), csrf=get_csrf(request))
    return templates.TemplateResponse(request, name, ctx, status_code=status_code)
