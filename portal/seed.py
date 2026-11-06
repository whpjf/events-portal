"""Учебные данные для портала: python seed.py (после alembic upgrade head)."""
from datetime import datetime, timedelta

from app.database import SessionLocal
from app.models import Application, Event, Review, User
from app.security import hash_password

EVENTS = [
    # (картинка, название, через сколько дней, место, описание)
    ("bees", "Пчеловодство: первый сезон", -48,
     "Библиотека №14, Ленинский проспект, 61",
     "Разбор первого сезона на пасеке: как подготовить улей, когда ставить рамки, как не бояться пчёл. Показываем дымарь и защитную одежду."),
    ("pottery", "Гончарный круг для начинающих", -27,
     "Мастерская «Глина», Нагорная улица, 7",
     "Три часа у круга: центровка, вытягивание стенок, первая чашка. Глина и фартуки выдаются, готовые изделия обжигаются через неделю."),
    ("bread", "Закваска и хлеб дома", -12,
     "Школа кулинарии «Мука», Пятницкая улица, 22",
     "Как завести закваску, сколько ей кормиться и почему хлеб в чугунной форме выходит с корочкой. В конце дегустация."),
    ("binding", "Переплёт книги вручную", 9,
     "Библиотека №14, Ленинский проспект, 61",
     "Сшиваем тетрадь на нитках, делаем обложку из картона и ткани. Принесите старую книгу, которую жалко выбросить."),
    ("birds", "Городские птицы зимой", 16,
     "Парк «Зарядье», вход со стороны Варварки",
     "Двухчасовая прогулка с биноклями. Учимся различать синиц, снегирей и свиристелей по силуэту и голосу."),
    ("weather", "Домашняя метеостанция", 23,
     "Коворкинг «Ось», Автозаводская улица, 18",
     "Собираем датчик температуры и давления, записываем данные за сутки и строим график. Паяльник не нужен."),
    ("bike", "Велосипед в городе зимой", 30,
     "Велоцентр на Лужнецкой набережной, 2/4",
     "Шины, смазка, одежда и маршруты на снегу. Разбираем, как подготовить велосипед к морозу и где его оставлять на ночь."),
    ("astro", "Звёздный вечер: любительская астрономия", 44,
     "Поляна у пруда, Измайловский парк",
     "Смотрим на Луну и планеты в телескопы, говорим про красный свет и тёмное небо. Приезжайте в тёплой одежде."),
]


def run():
    db = SessionLocal()
    if db.query(Event).count():
        print("В базе уже есть данные, ничего не добавляю")
        return
    now = datetime.now().replace(minute=0, second=0, microsecond=0)
    events = []
    for image, title, days, place, text in EVENTS:
        e = Event(title=title, event_date=now.replace(hour=18) + timedelta(days=days), place=place, description=text, image=image + ".jpg")
        db.add(e)
        events.append(e)
    admin = User(login="admin_konf", password_hash=hash_password("Admin2026Konf"), email="admin@konferencii.test", phone="+79160000001", role="admin")
    anna = User(login="anna_k", password_hash=hash_password("Parol2026Anna"), email="anna@mail.test", phone="+79161112233")
    oleg = User(login="oleg_s", password_hash=hash_password("Parol2026Oleg"), email="oleg@mail.test", phone="+79162223344")
    db.add_all([admin, anna, oleg])
    db.commit()
    rows = [
        (anna, events[0], "done", "Малый зал", "Банковская карта"),
        (anna, events[2], "done", "Кухня-студия", "Наличные при входе"),
        (anna, events[3], "assigned", "Читальный зал", "Банковская карта"),
        (oleg, events[1], "done", "Мастерская", "Перевод по номеру телефона"),
        (oleg, events[3], "new", "Читальный зал", "Наличные при входе"),
        (oleg, events[5], "new", "Основной зал", "Банковская карта"),
    ]
    apps = []
    for user, event, status, room, payment in rows:
        a = Application(user_id=user.id, event_id=event.id, status=status, room=room, payment=payment, created_at=now - timedelta(days=5))
        db.add(a)
        apps.append(a)
    db.commit()
    db.add(Review(application_id=apps[0].id, rating=5, body="Показали дымарь и рамки вживую, наконец понятно, с чего начинать. Хватило времени на вопросы.",
                  created_at=now - timedelta(days=40)))
    db.add(Review(application_id=apps[3].id, rating=4, body="Первая чашка вышла кривой, но мастер помог, и она не развалилась. Мало было времени на глазурь.",
                  created_at=now - timedelta(days=20)))
    db.commit()
    print("Добавлено: мероприятий %d, пользователей 3, заявок %d" % (len(events), len(rows)))


if __name__ == "__main__":
    run()
