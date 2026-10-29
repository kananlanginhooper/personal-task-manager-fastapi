"""Baseline: the schema as the app created it before Alembic.

Creates only the tables that don't exist yet, so running it on a database the app already set up just records the
revision. Later changes get their own revisions (alembic revision --autogenerate -m "...").

Revision ID: 0001
Revises:
Create Date: 2026-10-29
"""

from alembic import op
from sqlalchemy import inspect

from app.db import models  # noqa: F401  (registers tables)
from app.db.session import Base

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    existing = set(inspect(bind).get_table_names())
    Base.metadata.create_all(bind, tables=[t for name, t in Base.metadata.tables.items() if name not in existing])


def downgrade() -> None:
    raise NotImplementedError("The baseline is not reversible: it would drop every table and its data.")
