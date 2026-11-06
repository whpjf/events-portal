"""уникальный логин без учёта регистра

Revision ID: 0005
Revises: 0004
"""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # если в базе уже есть Anna и anna, индекс не создастся: такие учётные записи придётся объединить вручную
    op.create_index("uq_users_login_lower", "users", [sa.text("lower(login)")], unique=True)


def downgrade() -> None:
    op.drop_index("uq_users_login_lower", table_name="users")
