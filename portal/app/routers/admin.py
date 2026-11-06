from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import admin_required
from app.security import verify_csrf
from app.services import ApplicationService
from app.templating import render

router = APIRouter(prefix="/admin")


@router.get("")
def admin_page(request: Request, db: Session = Depends(get_db), user=Depends(admin_required)):
    return render(request, "admin.html", user, applications=ApplicationService(db).all())


@router.post("/applications/{app_id}/status", dependencies=[Depends(verify_csrf)])
def change_status(
    request: Request, app_id: int, status: str = Form(""), db: Session = Depends(get_db), user=Depends(admin_required)
):
    ApplicationService(db).set_status(app_id, status)
    request.session["flash"] = "Статус изменён"
    return RedirectResponse("/admin", status_code=303)
