from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import login_required
from app.schemas import ApplicationForm, parse
from app.security import verify_csrf
from app.services import ApplicationService, EventService
from app.templating import render

router = APIRouter()


@router.get("/events/{event_id}/apply")
def apply_page(request: Request, event_id: int, db: Session = Depends(get_db), user=Depends(login_required)):
    event = EventService(db).get(event_id)
    if event is None:
        raise HTTPException(404)
    return render(request, "apply.html", user, event=event, errors={}, values={})


@router.post("/events/{event_id}/apply", dependencies=[Depends(verify_csrf)])
def apply(
    request: Request,
    event_id: int,
    room: str = Form(""),
    payment: str = Form(""),
    comment: str = Form(""),
    db: Session = Depends(get_db),
    user=Depends(login_required),
):
    event = EventService(db).get(event_id)
    if event is None:
        raise HTTPException(404)
    data = dict(room=room, payment=payment, comment=comment)
    form, errors = parse(ApplicationForm, data)
    service = ApplicationService(db)
    if form and service.exists(user.id, event.id):
        errors["form"] = "Вы уже подали заявку на это мероприятие"
    if errors:
        return render(request, "apply.html", user, status_code=422, event=event, errors=errors, values=data)
    service.create(user, event, form)
    request.session["flash"] = "Заявка отправлена"
    return RedirectResponse("/my", status_code=303)


@router.get("/my")
def my_applications(request: Request, db: Session = Depends(get_db), user=Depends(login_required)):
    return render(request, "my.html", user, applications=ApplicationService(db).of_user(user.id))
