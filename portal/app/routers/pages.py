from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import current_user
from app.services import EventService, ReviewService
from app.templating import render

router = APIRouter()


@router.get("/")
def index(request: Request, q: str = "", db: Session = Depends(get_db), user=Depends(current_user)):
    events = EventService(db).search(q)
    return render(request, "events.html", user, events=events, q=q)


@router.get("/events/{event_id}")
def event_page(request: Request, event_id: int, db: Session = Depends(get_db), user=Depends(current_user)):
    event = EventService(db).get(event_id)
    if event is None:
        raise HTTPException(404)
    return render(request, "event.html", user, event=event, reviews=ReviewService(db).for_event(event_id))
