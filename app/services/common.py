"""Helpers every service uses. Services raise these errors; app.main turns them into HTTP responses."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import Change, now


class NotFoundError(Exception):
    """→ 404"""


class InvalidRequestError(Exception):
    """→ 400"""


def new_id() -> str:
    return uuid.uuid4().hex[:20]


def iso_now() -> str:
    return now().isoformat() + "Z"


def add_days(date: str, n: int) -> str:
    return (datetime.strptime(date, "%Y-%m-%d") + timedelta(days=n)).strftime("%Y-%m-%d")


def get_or_404[T](db: Session, model: type[T], key: str) -> T:
    row = db.get(model, key)
    if row is None:
        raise NotFoundError(f"{model.__name__} {key} not found")
    return row


def log(db: Session, type_: str, title: str | None = None, **kw: Any) -> Change:
    """Add an entry to the append-only change log (committed with the caller's change)."""
    entry = Change(
        type=type_,
        title=title,
        task_id=kw.get("task_id"),
        project_id=kw.get("project_id"),
        from_=kw.get("from_"),
        to=kw.get("to"),
        reason=kw.get("reason") or None,
        extra=kw.get("extra"),
    )
    db.add(entry)
    return entry
