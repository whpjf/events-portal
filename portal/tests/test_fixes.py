"""Ошибки, найденные при тестировании (репозиторий events-portal-tests), и проверка, что они исправлены."""
import pytest

from tests.conftest import login, token

BASE = {"login": "tester_1", "email": "tester@mail.test", "phone": "+7 916 000-11-22", "password": "Parol2026Test", "password2": "Parol2026Test"}


def register(client, **fields):
    data = dict(BASE, **fields)
    data["csrf_token"] = token(client, "/register")
    return client.post("/register", data=data)


@pytest.mark.parametrize("path", ["/nope", "/events/abc", "/events/0", "/events/99999999999999999999", "/static/nothing.css"])
def test_wrong_address_gives_site_page(client, path):
    r = client.get(path)
    assert r.status_code == 404
    assert "text/html" in r.headers["content-type"]
    assert "Страница не найдена" in r.text


def test_wrong_method_gives_site_page(client):
    r = client.get("/logout")
    assert r.status_code == 405
    assert "text/html" in r.headers["content-type"]


@pytest.mark.parametrize("q", ["закваска", "ЗАКВАСКА", "хлеб дома"])
def test_search_ignores_case(client, q):
    assert "Закваска и хлеб дома" in client.get("/", params={"q": q}).text


def test_cannot_apply_to_past_event(client):
    login(client, "oleg_s", "Parol2026Oleg")
    assert client.get("/events/1/apply").status_code == 303
    t = token(client, "/my")
    r = client.post("/events/1/apply", data={"room": "Малый зал", "payment": "Банковская карта", "csrf_token": t})
    assert r.status_code == 422
    assert "уже прошло" in r.text


def test_login_is_unique_without_case(client):
    assert register(client, login="ANNA_K").status_code == 422


def test_login_with_other_case_signs_in(client):
    r = client.post("/login", data={"login": "ANNA_K", "password": "Parol2026Anna", "csrf_token": token(client)})
    assert r.status_code == 303


@pytest.mark.parametrize("field, value", [
    ("login", "tester" + chr(10)),
    ("password", " " * 8),
    ("password2", " " * 8),
    ("email", "a@b.c"),
    ("email", "a@mail.ru" + chr(10)),
    ("phone", "+7 " + "".join(chr(0x660 + int(d)) for d in "9161234567")),
])
def test_bad_values_are_rejected(client, field, value):
    fields = {field: value}
    if field == "password":
        fields["password2"] = value
    assert register(client, **fields).status_code == 422
