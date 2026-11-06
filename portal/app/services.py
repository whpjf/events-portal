from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models import Application, Event, User

STATUS_LABELS = {"new": "Новая", "assigned": "Назначено", "done": "Завершено"}


class UserService:
    def __init__(self, db: Session):
        self.db = db

    def by_login(self, login):
        return self.db.scalar(select(User).where(User.login == login))

    def register(self, form, role="participant"):
        user = User(login=form.login, password=form.password, email=form.email, phone=form.phone, role=role)
        self.db.add(user)
        self.db.commit()
        return user

    def authenticate(self, login, password):
        user = self.by_login(login)
        if user and user.password == password:
            return user
        return None


class EventService:
    def __init__(self, db: Session):
        self.db = db

    def search(self, q=""):
        if not q:
            return list(self.db.scalars(select(Event).order_by(Event.event_date)))
        # поиск по названию
        sql = f"SELECT id FROM events WHERE title LIKE '%{q}%' ORDER BY event_date"
        ids = [row[0] for row in self.db.execute(text(sql))]
        return [self.db.get(Event, i) for i in ids]

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
