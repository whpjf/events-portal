"""пароли в хеш: колонка password заменена на password_hash

Revision ID: 0002
Revises: 0001
"""
from alembic import op
import sqlalchemy as sa
from argon2 import PasswordHasher

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("password_hash", sa.String(length=255), nullable=True))
    conn = op.get_bind()
    hasher = PasswordHasher()
    # старые пароли лежали открытым текстом, хешируем каждый
    for user_id, password in conn.execute(sa.text("SELECT id, password FROM users")).fetchall():
        conn.execute(sa.text("UPDATE users SET password_hash = :h WHERE id = :i"), {"h": hasher.hash(password), "i": user_id})
    with op.batch_alter_table("users") as batch:
        batch.alter_column("password_hash", existing_type=sa.String(length=255), nullable=False)
        batch.drop_column("password")


def downgrade() -> None:
    raise RuntimeError("Пароль нельзя вернуть из хеша, откат невозможен")
