"""таблица статусов, связь заявок со статусами, ограничения целостности

Revision ID: 0004
Revises: 0003
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

STATUSES = [(1, "new", "Новая", 1), (2, "assigned", "Назначено", 2), (3, "done", "Завершено", 3)]


def upgrade() -> None:
    statuses = op.create_table(
        "statuses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("name", sa.String(30), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.UniqueConstraint("code", name="uq_statuses_code"),
    )
    op.bulk_insert(statuses, [dict(id=i, code=c, name=n, position=p) for i, c, n, p in STATUSES])

    # переносим данные: строковый статус заменяем ссылкой на таблицу статусов
    with op.batch_alter_table("applications") as batch:
        batch.add_column(sa.Column("status_id", sa.Integer(), nullable=True))
    op.execute("UPDATE applications SET status_id = (SELECT id FROM statuses WHERE statuses.code = applications.status)")
    with op.batch_alter_table("applications") as batch:
        batch.alter_column("status_id", existing_type=sa.Integer(), nullable=False)
        batch.create_foreign_key("fk_applications_status_id", "statuses", ["status_id"], ["id"])
        batch.create_unique_constraint("uq_applications_user_event", ["user_id", "event_id"])
        batch.create_index("ix_applications_user_id", ["user_id"])
        batch.create_index("ix_applications_event_id", ["event_id"])
        batch.create_index("ix_applications_status_id", ["status_id"])
        batch.drop_column("status")

    with op.batch_alter_table("reviews") as batch:
        batch.create_unique_constraint("uq_reviews_application", ["application_id"])
        batch.create_check_constraint("ck_reviews_rating", "rating BETWEEN 1 AND 5")


def downgrade() -> None:
    with op.batch_alter_table("reviews") as batch:
        batch.drop_constraint("ck_reviews_rating", type_="check")
        batch.drop_constraint("uq_reviews_application", type_="unique")
    with op.batch_alter_table("applications") as batch:
        batch.add_column(sa.Column("status", sa.String(20), nullable=True))
    op.execute("UPDATE applications SET status = (SELECT code FROM statuses WHERE statuses.id = applications.status_id)")
    with op.batch_alter_table("applications") as batch:
        batch.alter_column("status", existing_type=sa.String(20), nullable=False)
        batch.drop_index("ix_applications_status_id")
        batch.drop_index("ix_applications_event_id")
        batch.drop_index("ix_applications_user_id")
        batch.drop_constraint("uq_applications_user_event", type_="unique")
        batch.drop_constraint("fk_applications_status_id", type_="foreignkey")
        batch.drop_column("status_id")
    op.drop_table("statuses")
