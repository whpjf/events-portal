import sqlite3
import os

from tests.conftest import login, token


def status_of(app_id):
    con = sqlite3.connect(os.environ["PORTAL_DB"])
    row = con.execute("SELECT s.code FROM applications a JOIN statuses s ON s.id = a.status_id WHERE a.id = ?", (app_id,)).fetchone()
    con.close()
    return row[0]


def advance(client, app_id):
    return client.post(f"/admin/applications/{app_id}/advance", data={"csrf_token": token(client, "/admin")})


def test_status_goes_new_assigned_done(client):
    login(client, "admin_konf", "Admin2026Konf")
    assert status_of(5) == "new"
    assert advance(client, 5).status_code == 303
    assert status_of(5) == "assigned"
    advance(client, 5)
    assert status_of(5) == "done"


def test_done_application_does_not_move_further(client):
    login(client, "admin_konf", "Admin2026Konf")
    advance(client, 1)
    assert status_of(1) == "done"


def test_advance_unknown_application(client):
    login(client, "admin_konf", "Admin2026Konf")
    assert advance(client, 999).status_code == 404


def test_review_opens_after_admin_finishes_application(client):
    login(client, "admin_konf", "Admin2026Konf")
    advance(client, 3)
    assert status_of(3) == "done"
    client.post("/logout", data={"csrf_token": token(client, "/admin")})
    login(client, "anna_k", "Parol2026Anna")
    assert client.get("/my/3/review").status_code == 200


def event_data(**kw):
    data = {"title": "Новое занятие", "event_date": "2027-01-20T18:30", "place": "Библиотека №14",
            "description": "Описание не короче десяти символов", "image": "bees.jpg"}
    data.update(kw)
    return data


def test_admin_creates_edits_deletes_event(client):
    login(client, "admin_konf", "Admin2026Konf")
    t = token(client, "/admin/events/new")
    r = client.post("/admin/events/new", data=dict(event_data(), csrf_token=t))
    assert r.status_code == 303
    assert "Новое занятие" in client.get("/admin/events").text
    t = token(client, "/admin/events/9/edit")
    r = client.post("/admin/events/9/edit", data=dict(event_data(title="Занятие с новым названием"), csrf_token=t))
    assert r.status_code == 303
    assert "Занятие с новым названием" in client.get("/").text
    t = token(client, "/admin/events")
    assert client.post("/admin/events/9/delete", data={"csrf_token": t}).status_code == 303
    assert client.get("/events/9").status_code == 404


def test_event_form_errors(client):
    login(client, "admin_konf", "Admin2026Konf")
    t = token(client, "/admin/events/new")
    r = client.post("/admin/events/new", data=dict(event_data(title="ab", event_date="", image="x.jpg"), csrf_token=t))
    assert r.status_code == 422
    assert "Название: от 3 до 120 символов" in r.text
    assert "Укажите дату и время мероприятия" in r.text
    assert "Выберите фото из списка" in r.text


def test_event_with_applications_is_not_deleted(client):
    login(client, "admin_konf", "Admin2026Konf")
    t = token(client, "/admin/events")
    client.post("/admin/events/4/delete", data={"csrf_token": t})
    assert client.get("/events/4").status_code == 200


def test_participant_cannot_manage_events(client):
    login(client, "anna_k", "Parol2026Anna")
    assert client.get("/admin/events/new").status_code == 403
    t = token(client, "/my")
    assert client.post("/admin/events/4/delete", data={"csrf_token": t}).status_code == 403


def test_participant_edits_new_application(client):
    login(client, "oleg_s", "Parol2026Oleg")
    t = token(client, "/my/5/edit")
    r = client.post("/my/5/edit", data={"room": "Мастерская", "payment": "Банковская карта", "comment": "Изменил помещение", "csrf_token": t})
    assert r.status_code == 303
    assert "Мастерская" in client.get("/my").text


def test_participant_cancels_new_application(client):
    login(client, "oleg_s", "Parol2026Oleg")
    t = token(client, "/my")
    assert client.post("/my/5/cancel", data={"csrf_token": t}).status_code == 303
    assert client.get("/my/5/edit").status_code == 404


def test_cannot_cancel_application_after_assigned_or_of_other_user(client):
    login(client, "anna_k", "Parol2026Anna")
    t = token(client, "/my")
    client.post("/my/3/cancel", data={"csrf_token": t})
    assert status_of(3) == "assigned"
    assert client.post("/my/5/cancel", data={"csrf_token": t}).status_code == 404
