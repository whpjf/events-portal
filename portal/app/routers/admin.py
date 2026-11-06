from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import admin_required
from app.security import verify_csrf
from app.models import Event
from app.services import STATUS_LABELS, ApplicationService
from app.templating import render

router = APIRouter(prefix="/admin")


@router.get("")
def admin_page(
    request: Request,
    status: str = "",
    event: str = "",
    q: str = "",
    db: Session = Depends(get_db),
    user=Depends(admin_required),
):
    event_id = int(event) if event.isdigit() else None
    apps = ApplicationService(db).filtered(status, event_id, q)
    events = db.query(Event).order_by(Event.title).all()
    filters = dict(status=status, event=event, q=q)
    return render(request, "admin.html", user, applications=apps, events=events, filters=filters, statuses=STATUS_LABELS)


@router.post("/applications/{app_id}/status", dependencies=[Depends(verify_csrf)])
def change_status(
    request: Request, app_id: int, status: str = Form(""), db: Session = Depends(get_db), user=Depends(admin_required)
):
    ApplicationService(db).set_status(app_id, status)
    request.session["flash"] = "Статус изменён"
    return RedirectResponse("/admin", status_code=303)
