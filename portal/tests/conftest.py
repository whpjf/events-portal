import os
import re
import tempfile
from pathlib import Path

# база для тестов лежит во временной папке, настоящая portal.db не трогается
os.environ["PORTAL_DB"] = str(Path(tempfile.mkdtemp()) / "test.db")

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import seed  # noqa: E402
from app.database import engine  # noqa: E402
from app.main import app  # noqa: E402
from app.security import guard  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(autouse=True)
def fresh_db():
    """Перед каждым тестом база создаётся заново миграциями и заполняется учебными данными."""
    engine.dispose()
    db_file = Path(os.environ["PORTAL_DB"])
    if db_file.exists():
        db_file.unlink()
    command.upgrade(Config(str(ROOT / "alembic.ini")), "head")
    seed.run()
    guard.fails.clear()


@pytest.fixture
def client():
    return TestClient(app, follow_redirects=False)


def token(client, path="/login"):
    """Берёт csrf-токен со страницы с формой."""
    html = client.get(path).text
    return re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)


def login(client, user, password):
    return client.post("/login", data={"login": user, "password": password, "csrf_token": token(client)})
