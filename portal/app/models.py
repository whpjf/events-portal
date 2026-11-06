from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    login: Mapped[str] = mapped_column(String(30), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str] = mapped_column(String(20))
    role: Mapped[str] = mapped_column(String(20), default="participant")

    applications: Mapped[list["Application"]] = relationship(back_populates="user")


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(120))
    event_date: Mapped[datetime] = mapped_column(DateTime)
    place: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text)
    image: Mapped[str] = mapped_column(String(60), default="")

    applications: Mapped[list["Application"]] = relationship(back_populates="event")


class Status(Base):
    __tablename__ = "statuses"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20))
    name: Mapped[str] = mapped_column(String(30))
    position: Mapped[int] = mapped_column()

    __table_args__ = (UniqueConstraint("code", name="uq_statuses_code"),)


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (
        UniqueConstraint("application_id", name="uq_reviews_application"),
        CheckConstraint("rating BETWEEN 1 AND 5", name="ck_reviews_rating"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id"))
    rating: Mapped[int] = mapped_column()
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    application: Mapped["Application"] = relationship(back_populates="review")


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"))
    status_id: Mapped[int] = mapped_column(ForeignKey("statuses.id", name="fk_applications_status_id"))
    room: Mapped[str] = mapped_column(String(60))
    payment: Mapped[str] = mapped_column(String(40))
    comment: Mapped[str] = mapped_column(String(300), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    __table_args__ = (
        UniqueConstraint("user_id", "event_id", name="uq_applications_user_event"),
        Index("ix_applications_user_id", "user_id"),
        Index("ix_applications_event_id", "event_id"),
        Index("ix_applications_status_id", "status_id"),
    )

    user: Mapped["User"] = relationship(back_populates="applications")
    event: Mapped["Event"] = relationship(back_populates="applications")
    status_ref: Mapped["Status"] = relationship(lazy="joined")
    review: Mapped["Review | None"] = relationship(back_populates="application", uselist=False)


# Application.status возвращает код статуса, чтобы шаблоны и сервисы работали с понятными словами
Application.status = property(lambda self: self.status_ref.code)
