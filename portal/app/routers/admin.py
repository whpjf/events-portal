from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.choices import ACTION_LABELS, IMAGES
from app.database import get_db
from app.deps import admin_required
from app.models import Event
from app.schemas import EventForm, parse
from app.security import verify_csrf
from app.services import STATUS_LABELS, ApplicationService, EventService
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
    return render(request, "admin.html", user, applications=apps, events=events, filters=filters,
                  statuses=STATUS_LABELS, actions=ACTION_LABELS)


@router.post("/applications/{app_id}/advance", dependencies=[Depends(verify_csrf)])
def advance_status(request: Request, app_id: int, db: Session = Depends(get_db), user=Depends(admin_required)):
    service = ApplicationService(db)
    app = service.get(app_id)
    if app is None:
        raise HTTPException(404)
    if service.advance(app):
        request.session["flash"] = "Статус заявки № %d изменён" % app.id
    else:
        request.session["flash"] = "Заявка № %d уже завершена, статус не меняется" % app.id
    return RedirectResponse("/admin", status_code=303)


# мероприятия: список, создание, правка, удаление

@router.get("/events")
def events_list(request: Request, db: Session = Depends(get_db), user=Depends(admin_required)):
    return render(request, "admin_events.html", user, events=EventService(db).all())


@router.get("/events/new")
def event_new(request: Request, user=Depends(admin_required)):
    return render(request, "event_form.html", user, event=None, errors={}, values={}, images=IMAGES)


@router.post("/events/new", dependencies=[Depends(verify_csrf)])
def event_create(
    request: Request,
    title: str = Form(""),
    event_date: str = Form(""),
    place: str = Form(""),
    description: str = Form(""),
    image: str = Form(""),
    db: Session = Depends(get_db),
    user=Depends(admin_required),
):
    data = dict(title=title, event_date=event_date, place=place, description=description, image=image)
    form, errors = parse(EventForm, data)
    if errors:
        return render(request, "event_form.html", user, status_code=422, event=None, errors=errors, values=data, images=IMAGES)
    EventService(db).create(form)
    request.session["flash"] = "Мероприятие добавлено"
    return RedirectResponse("/admin/events", status_code=303)


@router.get("/events/{event_id}/edit")
def event_edit(request: Request, event_id: int, db: Session = Depends(get_db), user=Depends(admin_required)):
    event = EventService(db).get(event_id)
    if event is None:
        raise HTTPException(404)
    values = dict(title=event.title, event_date=event.event_date.strftime("%Y-%m-%dT%H:%M"), place=event.place,
                  description=event.description, image=event.image)
    return render(request, "event_form.html", user, event=event, errors={}, values=values, images=IMAGES)


@router.post("/events/{event_id}/edit", dependencies=[Depends(verify_csrf)])
def event_update(
    request: Request,
    event_id: int,
    title: str = Form(""),
    event_date: str = Form(""),
    place: str = Form(""),
    description: str = Form(""),
    image: str = Form(""),
    db: Session = Depends(get_db),
    user=Depends(admin_required),
):
    service = EventService(db)
    event = service.get(event_id)
    if event is None:
        raise HTTPException(404)
    data = dict(title=title, event_date=event_date, place=place, description=description, image=image)
    form, errors = parse(EventForm, data)
    if errors:
        return render(request, "event_form.html", user, status_code=422, event=event, errors=errors, values=data, images=IMAGES)
    service.update(event, form)
    request.session["flash"] = "Изменения сохранены"
    return RedirectResponse("/admin/events", status_code=303)


@router.post("/events/{event_id}/delete", dependencies=[Depends(verify_csrf)])
def event_delete(request: Request, event_id: int, db: Session = Depends(get_db), user=Depends(admin_required)):
    service = EventService(db)
    event = service.get(event_id)
    if event is None:
        raise HTTPException(404)
    if service.delete(event):
        request.session["flash"] = "Мероприятие удалено"
    else:
        request.session["flash"] = "Удалить нельзя: на мероприятие уже есть заявки"
    return RedirectResponse("/admin/events", status_code=303)
