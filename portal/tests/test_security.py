import sqlite3
import os

from app.security import guard
from tests.conftest import login, token


def test_password_is_hashed():
    con = sqlite3.connect(os.environ["PORTAL_DB"])
    rows = con.execute("SELECT login, password_hash FROM users").fetchall()
    con.close()
    assert rows
    for _, h in rows:
        assert h.startswith("$argon2")


def test_search_injection_finds_nothing(client):
    page = client.get("/", params={"q": "zzz%' OR 1=1 --"})
    assert page.status_code == 200
    assert "Ничего не найдено" in page.text


def test_search_quote_does_not_break(client):
    assert client.get("/", params={"q": "'"}).status_code == 200


def test_post_without_csrf_is_rejected(client):
    r = client.post("/login", data={"login": "anna_k", "password": "Parol2026Anna"})
    assert r.status_code == 403


def test_status_change_without_csrf_is_rejected(client):
    login(client, "admin_konf", "Admin2026Konf")
    r = client.post("/admin/applications/1/status", data={"status": "new"})
    assert r.status_code == 403


def test_guest_goes_to_login(client):
    for path in ("/my", "/admin", "/events/1/apply"):
        r = client.get(path)
        assert r.status_code == 303 and r.headers["location"].startswith("/login")


def test_participant_cannot_open_admin(client):
    login(client, "anna_k", "Parol2026Anna")
    assert client.get("/admin").status_code == 403


def test_participant_cannot_change_status(client):
    login(client, "anna_k", "Parol2026Anna")
    r = client.post("/admin/applications/1/status", data={"status": "new", "csrf_token": token(client, "/my")})
    assert r.status_code == 403


def test_admin_can_open_admin(client):
    login(client, "admin_konf", "Admin2026Konf")
    assert client.get("/admin").status_code == 200


def test_login_is_blocked_after_five_failures(client):
    for _ in range(5):
        r = client.post("/login", data={"login": "oleg_s", "password": "wrong-password", "csrf_token": token(client)})
        assert r.status_code == 401
    r = client.post("/login", data={"login": "oleg_s", "password": "Parol2026Oleg", "csrf_token": token(client)})
    assert r.status_code == 429


def test_session_cookie_flags(client):
    r = login(client, "anna_k", "Parol2026Anna")
    cookie = r.headers["set-cookie"].lower()
    assert "httponly" in cookie
    assert "samesite=lax" in cookie


def test_search_text_is_escaped(client):
    page = client.get("/", params={"q": '"><script>alert(1)</script>'})
    assert "<script>alert(1)</script>" not in page.text


def test_error_page_keeps_login_in_header(client):
    login(client, "anna_k", "Parol2026Anna")
    page = client.get("/admin")
    assert page.status_code == 403
    assert "anna_k" in page.text
