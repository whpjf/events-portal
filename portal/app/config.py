import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings:
    # база по умолчанию лежит в portal/data, для тестов путь меняется переменной PORTAL_DB
    db_path = os.environ.get("PORTAL_DB", str(BASE_DIR / "data" / "portal.db"))
    secret_key = os.environ.get("PORTAL_SECRET", "uchebnyj-klyuch-dlya-razrabotki")
    session_hours = 2


settings = Settings()
