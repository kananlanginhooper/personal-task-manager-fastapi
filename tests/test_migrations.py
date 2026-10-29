"""The Alembic baseline builds the same schema as the models, and is safe on a database the app already set up."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile

from sqlalchemy import create_engine, inspect


def _upgrade(url: str) -> None:
    env = {**os.environ, "DATABASE_URL": url}
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True, env=env, capture_output=True)


def _schema(url: str) -> dict[str, set[str]]:
    insp = inspect(create_engine(url))
    return {t: {c["name"] for c in insp.get_columns(t)} for t in insp.get_table_names() if t != "alembic_version"}


def test_baseline_matches_models_and_is_idempotent():
    from app.db import models  # noqa: F401
    from app.db.session import Base

    url = "sqlite:///" + os.path.join(tempfile.mkdtemp(), "m.db")
    _upgrade(url)
    expected = {name: {c.name for c in t.columns} for name, t in Base.metadata.tables.items()}
    assert _schema(url) == expected

    # An existing database (tables made by create_all, no alembic_version) only gets the revision recorded.
    url2 = "sqlite:///" + os.path.join(tempfile.mkdtemp(), "existing.db")
    Base.metadata.create_all(create_engine(url2))
    _upgrade(url2)
    assert _schema(url2) == expected
    assert "alembic_version" in inspect(create_engine(url2)).get_table_names()
