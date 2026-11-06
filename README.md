# Конференции.РФ

Учебный портал мероприятий: гость смотрит афишу, участник регистрируется и подаёт заявки, администратор меняет статусы заявок.
Сделан в рамках МДК.09.01 «Проектирование и разработка веб-приложений».

Стек: Python 3.12, FastAPI, Jinja2, SQLAlchemy 2 (SQLite), Alembic.

## Как запустить

```
cd portal
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\alembic upgrade head
.venv\Scripts\python seed.py
.venv\Scripts\python -m uvicorn app.main:app --port 8103
```
Сайт откроется на http://localhost:8103

## Учебные учётные записи

| Роль | Логин | Пароль |
|---|---|---|
| Администратор | admin_konf | Admin2026Konf |
| Участник | anna_k | Parol2026Anna |
| Участник | oleg_s | Parol2026Oleg |

## Папки

- `portal/` код портала (`app/` приложение, `migrations/` миграции Alembic, `seed.py` учебные данные)
- `Практика NN. Название/` по папке на каждую практику: README и скриншоты

## Практики

| № | Тема |
|---|---|
| 2 | Проектирование базы данных, ER-диаграмма |
| 3 | Модули ИС по ТЗ: регистрация, вход, заявки, панель администратора |
| 4 | Подсистема безопасности: хеши паролей, CSRF, права, сессии |
