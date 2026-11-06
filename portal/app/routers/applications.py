from datetime import datetime

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import RecordId, login_required
from app.choices import PAYMENTS, ROOMS
from app.schemas import ApplicationForm, ReviewForm, parse
from app.security import verify_csrf
from app.services import ApplicationService, EventService, ReviewService
from app.templating import render

router = APIRouter()


@router.get("/events/{event_id}/apply")
def apply_page(request: Request, event_id: RecordId, db: Session = Depends(get_db), user=Depends(login_required)):
    event = EventService(db).get(event_id)
    if event is None:
        raise HTTPException(404)
    if event.event_date < datetime.now():
        request.session["flash"] = "Мероприятие уже прошло, заявки не принимаются"
        return RedirectResponse(f"/events/{event.id}", status_code=303)
    return render(request, "apply.html", user, event=event, errors={}, values={}, rooms=ROOMS, payments=PAYMENTS)


@router.post("/events/{event_id}/apply", dependencies=[Depends(verify_csrf)])
def apply(
    request: Request,
    event_id: RecordId,
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
    if event.event_date < datetime.now():
        errors["form"] = "Мероприятие уже прошло, заявки не принимаются"
    elif form and service.exists(user.id, event.id):
        errors["form"] = "Вы уже подали заявку на это мероприятие"
    if errors:
        return render(request, "apply.html", user, status_code=422, event=event, errors=errors, values=data, rooms=ROOMS, payments=PAYMENTS)
    service.create(user, event, form)
    request.session["flash"] = "Заявка отправлена"
    return RedirectResponse("/my", status_code=303)


@router.get("/my")
def my_applications(request: Request, db: Session = Depends(get_db), user=Depends(login_required)):
    return render(request, "my.html", user, applications=ApplicationService(db).of_user(user.id))


def own_new_application(db, app_id, user):
    """Менять и отменять можно только свою заявку и пока она новая."""
    app = ApplicationService(db).get(app_id)
    if app is None or app.user_id != user.id:
        raise HTTPException(404)
    return app


@router.get("/my/{app_id}/edit")
def application_edit(request: Request, app_id: RecordId, db: Session = Depends(get_db), user=Depends(login_required)):
    app = own_new_application(db, app_id, user)
    if app.status != "new":
        request.session["flash"] = "Заявку можно менять, пока она новая"
        return RedirectResponse("/my", status_code=303)
    values = dict(room=app.room, payment=app.payment, comment=app.comment)
    return render(request, "apply.html", user, event=app.event, errors={}, values=values, rooms=ROOMS, payments=PAYMENTS,
                  action=f"/my/{app.id}/edit", title="Изменение заявки", button="Сохранить")


@router.post("/my/{app_id}/edit", dependencies=[Depends(verify_csrf)])
def application_update(
    request: Request,
    app_id: RecordId,
    room: str = Form(""),
    payment: str = Form(""),
    comment: str = Form(""),
    db: Session = Depends(get_db),
    user=Depends(login_required),
):
    app = own_new_application(db, app_id, user)
    if app.status != "new":
        request.session["flash"] = "Заявку можно менять, пока она новая"
        return RedirectResponse("/my", status_code=303)
    data = dict(room=room, payment=payment, comment=comment)
    form, errors = parse(ApplicationForm, data)
    if errors:
        return render(request, "apply.html", user, status_code=422, event=app.event, errors=errors, values=data, rooms=ROOMS,
                      payments=PAYMENTS, action=f"/my/{app.id}/edit", title="Изменение заявки", button="Сохранить")
    ApplicationService(db).update(app, form)
    request.session["flash"] = "Заявка изменена"
    return RedirectResponse("/my", status_code=303)


@router.post("/my/{app_id}/cancel", dependencies=[Depends(verify_csrf)])
def application_cancel(request: Request, app_id: RecordId, db: Session = Depends(get_db), user=Depends(login_required)):
    app = own_new_application(db, app_id, user)
    if app.status != "new":
        request.session["flash"] = "Отменить можно только новую заявку"
        return RedirectResponse("/my", status_code=303)
    ApplicationService(db).cancel(app)
    request.session["flash"] = "Заявка отменена"
    return RedirectResponse("/my", status_code=303)


@router.get("/cabinet")
def cabinet(request: Request, db: Session = Depends(get_db), user=Depends(login_required)):
    apps = ApplicationService(db).of_user(user.id)
    stats = {
        "total": len(apps),
        "done": len([a for a in apps if a.status == "done"]),
        "reviews": len([a for a in apps if a.review]),
    }
    return render(request, "cabinet.html", user, stats=stats)


def own_done_application(db, app_id, user):
    """Заявка должна быть своей и завершённой, иначе отзыв оставить нельзя."""
    app = ApplicationService(db).get(app_id)
    if app is None or app.user_id != user.id:
        raise HTTPException(404)
    return app


@router.get("/my/{app_id}/review")
def review_page(request: Request, app_id: RecordId, db: Session = Depends(get_db), user=Depends(login_required)):
    app = own_done_application(db, app_id, user)
    if app.status != "done" or app.review:
        request.session["flash"] = "Отзыв можно оставить один раз и только после завершения мероприятия"
        return RedirectResponse("/my", status_code=303)
    return render(request, "review.html", user, app=app, errors={}, values={})


@router.post("/my/{app_id}/review", dependencies=[Depends(verify_csrf)])
def review_create(
    request: Request,
    app_id: RecordId,
    rating: str = Form(""),
    body: str = Form(""),
    db: Session = Depends(get_db),
    user=Depends(login_required),
):
    app = own_done_application(db, app_id, user)
    if app.status != "done" or app.review:
        request.session["flash"] = "Отзыв можно оставить один раз и только после завершения мероприятия"
        return RedirectResponse("/my", status_code=303)
    data = dict(rating=rating, body=body)
    form, errors = parse(ReviewForm, data)
    if errors:
        return render(request, "review.html", user, status_code=422, app=app, errors=errors, values=data)
    ReviewService(db).create(app, form)
    request.session["flash"] = "Спасибо, отзыв сохранён"
    return RedirectResponse("/my", status_code=303)
