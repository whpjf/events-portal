from logging.config import fileConfig

from alembic import context

from app.database import Base, engine
from app import models  # noqa: F401  (модели нужны, чтобы Alembic видел таблицы)

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(url=str(engine.url), target_metadata=target_metadata, literal_binds=True, render_as_batch=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    # SQLite не умеет менять столбцы на месте, поэтому render_as_batch
    with engine.connect() as connection:
        # при пересоздании таблицы (batch) проверка внешних ключей мешает, на время миграции выключаем,
        # а после миграции проверяем всю базу целиком
        connection.exec_driver_sql("PRAGMA foreign_keys = OFF")
        context.configure(connection=connection, target_metadata=target_metadata, render_as_batch=True)
        with context.begin_transaction():
            context.run_migrations()
        connection.commit()
        broken = connection.exec_driver_sql("PRAGMA foreign_key_check").fetchall()
        if broken:
            raise RuntimeError("После миграции нарушены внешние ключи: %s" % broken)
        connection.commit()
        connection.exec_driver_sql("PRAGMA foreign_keys = ON")


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
