import os
import sqlite3

import pytest
from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal
from app.models import Application, Review


def sql(query, *args):
    con = sqlite3.connect(os.environ["PORTAL_DB"])
    try:
        return con.execute(query, args).fetchall()
    finally:
        con.close()


def test_statuses_table_is_filled():
    rows = sql("SELECT code, name, position FROM statuses ORDER BY position")
    assert rows == [("new", "Новая", 1), ("assigned", "Назначено", 2), ("done", "Завершено", 3)]


def test_foreign_key_check_is_empty():
    assert sql("PRAGMA foreign_key_check") == []
    assert sql("PRAGMA integrity_check") == [("ok",)]


def test_application_needs_existing_event():
    db = SessionLocal()
    db.add(Application(user_id=2, event_id=999, status_id=1, room="Малый зал", payment="Банковская карта"))
    with pytest.raises(IntegrityError):
        db.commit()
    db.close()


def test_application_needs_existing_status():
    db = SessionLocal()
    db.add(Application(user_id=2, event_id=7, status_id=42, room="Малый зал", payment="Банковская карта"))
    with pytest.raises(IntegrityError):
        db.commit()
    db.close()


def test_one_application_per_user_and_event():
    db = SessionLocal()
    db.add(Application(user_id=2, event_id=1, status_id=1, room="Малый зал", payment="Банковская карта"))
    with pytest.raises(IntegrityError):
        db.commit()
    db.close()


def test_one_review_per_application():
    db = SessionLocal()
    db.add(Review(application_id=1, rating=3, body="Второй отзыв на ту же заявку"))
    with pytest.raises(IntegrityError):
        db.commit()
    db.close()


def test_rating_is_between_1_and_5():
    db = SessionLocal()
    db.add(Review(application_id=2, rating=7, body="Оценка вне диапазона"))
    with pytest.raises(IntegrityError):
        db.commit()
    db.close()


def test_event_with_applications_cannot_be_deleted_in_database():
    db = SessionLocal()
    from app.models import Event
    db.delete(db.get(Event, 1))
    with pytest.raises(IntegrityError):
        db.commit()
    db.close()
