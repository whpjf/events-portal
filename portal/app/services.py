from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.choices import NEXT_STATUS
from app.models import Application, Event, Review, Status, User
from app.security import hash_password, verify_password

STATUS_LABELS = {"new": "Новая", "assigned": "Назначено", "done": "Завершено"}


class UserService:
    def __init__(self, db: Session):
        self.db = db

    def by_login(self, login):
        return self.db.scalar(select(User).where(User.login == login))

    def register(self, form, role="participant"):
        user = User(login=form.login, password_hash=hash_password(form.password), email=form.email, phone=form.phone, role=role)
        self.db.add(user)
        self.db.commit()
        return user

    def authenticate(self, login, password):
        user = self.by_login(login)
        if user and verify_password(user.password_hash, password):
            return user
        return None


class EventService:
    def __init__(self, db: Session):
        self.db = db

    def search(self, q=""):
        query = select(Event).order_by(Event.event_date)
        if q:
            # поиск по названию, значение q подставляется параметром, а не строкой
            query = query.where(Event.title.like(f"%{q}%"))
        return self.upcoming_first(list(self.db.scalars(query)))

    @staticmethod
    def upcoming_first(events):
        """Сначала будущие по возрастанию даты, потом прошедшие, самые свежие первыми."""
        now = datetime.now()
        future = [e for e in events if e.event_date >= now]
        past = sorted((e for e in events if e.event_date < now), key=lambda e: e.event_date, reverse=True)
        return future + past

    def get(self, event_id):
        return self.db.get(Event, event_id)

    def all(self):
        return list(self.db.scalars(select(Event).order_by(Event.event_date.desc())))

    def create(self, form):
        event = Event(title=form.title, event_date=form.event_date, place=form.place, description=form.description, image=form.image)
        self.db.add(event)
        self.db.commit()
        return event

    def update(self, event, form):
        event.title, event.event_date, event.place = form.title, form.event_date, form.place
        event.description, event.image = form.description, form.image
        self.db.commit()

    def delete(self, event):
        """Мероприятие с заявками удалять нельзя, иначе заявки останутся без мероприятия."""
        if event.applications:
            return False
        self.db.delete(event)
        self.db.commit()
        return True


class ApplicationService:
    def __init__(self, db: Session):
        self.db = db

    def exists(self, user_id, event_id):
        return self.db.scalar(
            select(Application).where(Application.user_id == user_id, Application.event_id == event_id)
        ) is not None

    def create(self, user, event, form):
        new_status = self.db.scalar(select(Status).where(Status.code == "new"))
        app = Application(user_id=user.id, event_id=event.id, status_id=new_status.id, room=form.room, payment=form.payment,
                          comment=form.comment)
        self.db.add(app)
        self.db.commit()
        return app

    def of_user(self, user_id):
        q = select(Application).where(Application.user_id == user_id).order_by(Application.created_at.desc())
        return list(self.db.scalars(q))

    def get(self, app_id):
        return self.db.get(Application, app_id)

    def filtered(self, status="", event_id=None, q=""):
        """Заявки для панели администратора с фильтрами по статусу, мероприятию и логину."""
        query = select(Application).join(User).order_by(Application.created_at.desc())
        if status in STATUS_LABELS:
            query = query.join(Status).where(Status.code == status)
        if event_id:
            query = query.where(Application.event_id == event_id)
        if q:
            query = query.where(User.login.like(f"%{q}%"))
        return list(self.db.scalars(query))

    def advance(self, app):
        """Статус меняется только вперёд: новая, назначено, завершено."""
        nxt = NEXT_STATUS.get(app.status)
        if nxt is None:
            return False
        app.status_id = self.db.scalar(select(Status.id).where(Status.code == nxt))
        self.db.commit()
        return True

    def update(self, app, form):
        app.room, app.payment, app.comment = form.room, form.payment, form.comment
        self.db.commit()

    def cancel(self, app):
        self.db.delete(app)
        self.db.commit()


class ReviewService:
    def __init__(self, db: Session):
        self.db = db

    def exists(self, app_id):
        return self.db.scalar(select(Review).where(Review.application_id == app_id)) is not None

    def create(self, application, form):
        review = Review(application_id=application.id, rating=form.rating, body=form.body)
        self.db.add(review)
        self.db.commit()
        return review

    def for_event(self, event_id):
        query = select(Review).join(Application).where(Application.event_id == event_id).order_by(Review.created_at.desc())
        return list(self.db.scalars(query))
