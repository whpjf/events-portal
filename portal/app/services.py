from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Application, Event, User
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
        if not q:
            return list(self.db.scalars(select(Event).order_by(Event.event_date)))
        # поиск по названию, значение q подставляется параметром, а не строкой
        query = select(Event).where(Event.title.like(f"%{q}%")).order_by(Event.event_date)
        return list(self.db.scalars(query))

    def get(self, event_id):
        return self.db.get(Event, event_id)


class ApplicationService:
    def __init__(self, db: Session):
        self.db = db

    def exists(self, user_id, event_id):
        return self.db.scalar(
            select(Application).where(Application.user_id == user_id, Application.event_id == event_id)
        ) is not None

    def create(self, user, event, form):
        app = Application(user_id=user.id, event_id=event.id, room=form.room, payment=form.payment, comment=form.comment)
        self.db.add(app)
        self.db.commit()
        return app

    def of_user(self, user_id):
        q = select(Application).where(Application.user_id == user_id).order_by(Application.created_at.desc())
        return list(self.db.scalars(q))

    def all(self):
        return list(self.db.scalars(select(Application).order_by(Application.created_at.desc())))

    def set_status(self, app_id, status):
        app = self.db.get(Application, app_id)
        if app and status in STATUS_LABELS:
            app.status = status
            self.db.commit()
        return app
