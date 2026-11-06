from tests.conftest import login, token


def apply(client, event_id, room="Малый зал", payment="Банковская карта", comment=""):
    t = token(client, f"/events/{event_id}/apply")
    return client.post(f"/events/{event_id}/apply", data={"room": room, "payment": payment, "comment": comment, "csrf_token": t})


def test_register_shows_errors_next_to_fields(client):
    t = token(client, "/register")
    r = client.post("/register", data={"login": "an", "email": "x", "phone": "1", "password": "123", "password2": "1", "csrf_token": t})
    assert r.status_code == 422
    assert r.text.count('class="field-error"') >= 5
    assert "Пароль: не короче 8 символов" in r.text


def test_register_ok_and_phone_normalized(client):
    t = token(client, "/register")
    r = client.post("/register", data={"login": "new_user", "email": "n@mail.test", "phone": "8 (916) 555-12-34",
                                        "password": "Parol2026New", "password2": "Parol2026New", "csrf_token": t})
    assert r.status_code == 303
    page = client.get("/cabinet")
    assert "+79165551234" in page.text


def test_application_room_must_be_from_list(client):
    login(client, "oleg_s", "Parol2026Oleg")
    r = apply(client, 7, room="Подвал")
    assert r.status_code == 422
    assert "Выберите помещение из списка" in r.text


def test_application_ok(client):
    login(client, "oleg_s", "Parol2026Oleg")
    r = apply(client, 7)
    assert r.status_code == 303
    assert "Велосипед в городе зимой" in client.get("/my").text


def test_second_application_for_same_event_is_rejected(client):
    login(client, "oleg_s", "Parol2026Oleg")
    assert apply(client, 7).status_code == 303
    assert apply(client, 7).status_code == 422


def test_review_not_available_before_done(client):
    login(client, "anna_k", "Parol2026Anna")
    # заявка 3 у anna_k имеет статус «назначено»
    r = client.get("/my/3/review")
    assert r.status_code == 303 and r.headers["location"] == "/my"


def test_review_after_done(client):
    login(client, "anna_k", "Parol2026Anna")
    page = client.get("/my/2/review")
    assert page.status_code == 200
    t = token(client, "/my/2/review")
    r = client.post("/my/2/review", data={"rating": "5", "body": "Хлеб получился, закваска живёт", "csrf_token": t})
    assert r.status_code == 303
    assert "Хлеб получился" in client.get("/events/3").text
    # второй отзыв на ту же заявку не принимается
    assert client.get("/my/2/review").status_code == 303


def test_review_validation(client):
    login(client, "anna_k", "Parol2026Anna")
    t = token(client, "/my/2/review")
    r = client.post("/my/2/review", data={"rating": "9", "body": "ок", "csrf_token": t})
    assert r.status_code == 422
    assert "Оценка от 1 до 5" in r.text


def test_cannot_review_someone_elses_application(client):
    login(client, "oleg_s", "Parol2026Oleg")
    assert client.get("/my/1/review").status_code == 404


def test_admin_filter_by_status(client):
    login(client, "admin_konf", "Admin2026Konf")
    page = client.get("/admin", params={"status": "new"})
    assert "Найдено заявок: 2" in page.text
    page = client.get("/admin", params={"status": "done"})
    assert "Найдено заявок: 3" in page.text


def test_admin_filter_empty_event_does_not_break(client):
    login(client, "admin_konf", "Admin2026Konf")
    r = client.get("/admin", params={"status": "", "event": "", "q": ""})
    assert r.status_code == 200
    assert "Найдено заявок: 6" in r.text


def test_admin_filter_by_login(client):
    login(client, "admin_konf", "Admin2026Konf")
    assert "Найдено заявок: 3" in client.get("/admin", params={"q": "oleg"}).text
