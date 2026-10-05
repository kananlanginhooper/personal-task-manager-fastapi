"""Database tables.

Everything a person types (areas, habits, tasks, trophies, wording) lives in these tables,
never in the code. JSON columns hold small nested lists (task steps, estimate history, moves).
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import inspect as sa_inspect
from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


def now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _camel(name: str) -> str:
    return re.sub(r"_([a-z])", lambda m: m.group(1).upper(), name)


def _snake(name: str) -> str:
    return re.sub(r"([A-Z])", lambda m: "_" + m.group(1).lower(), name)


class ApiMixin:
    """Converts rows to and from the camelCase JSON the front end uses."""

    @classmethod
    def _attr_keys(cls) -> list[str]:
        return [a.key for a in sa_inspect(cls).column_attrs]

    def to_api(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key in self._attr_keys():
            value = getattr(self, key)
            if isinstance(value, datetime):
                value = value.isoformat() + "Z"
            out[_camel(key)] = value
        return out

    def apply(self, data: dict[str, Any]) -> None:
        keys = set(self._attr_keys())
        for key, value in data.items():
            attr = _snake(key)
            if attr in keys:
                setattr(self, attr, value)


class Area(ApiMixin, Base):
    __tablename__ = "areas"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    color: Mapped[str] = mapped_column(String(32), default="#1E6A50")
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sort: Mapped[int] = mapped_column(Integer, default=0)


class HabitDef(ApiMixin, Base):
    __tablename__ = "habit_defs"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    group_name: Mapped[str] = mapped_column(String(80))
    name: Mapped[str] = mapped_column(String(120))
    sub: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    cheer: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    big: Mapped[bool] = mapped_column(Boolean, default=False)
    hype: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    sort: Mapped[int] = mapped_column(Integer, default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class HabitDay(ApiMixin, Base):
    """One row per calendar day: {habitId: true/false}."""

    __tablename__ = "habit_days"
    date: Mapped[str] = mapped_column(String(10), primary_key=True)
    marks: Mapped[dict] = mapped_column(JSON, default=dict)


class Task(ApiMixin, Base):
    __tablename__ = "tasks"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    date: Mapped[str] = mapped_column(String(10), index=True)
    start: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    est: Mapped[int] = mapped_column(Integer, default=15)
    orig_est: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    travel: Mapped[int] = mapped_column(Integer, default=0)
    close_by: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    leave: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    area: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    kind: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cheer: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    hype: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    cost: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    locked: Mapped[bool] = mapped_column(Boolean, default=False)
    recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    remind: Mapped[bool] = mapped_column(Boolean, default=False)
    work: Mapped[bool] = mapped_column(Boolean, default=False)
    big: Mapped[bool] = mapped_column(Boolean, default=False)
    dread: Mapped[bool] = mapped_column(Boolean, default=False)
    done: Mapped[bool] = mapped_column(Boolean, default=False)
    done_at: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    steps: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    est_history: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    moves: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    split_from: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)


class Project(ApiMixin, Base):
    __tablename__ = "projects"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    area: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    title: Mapped[str] = mapped_column(String(255))
    prio: Mapped[str] = mapped_column(String(16), default="steady")
    est: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    due: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    next: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sort: Mapped[int] = mapped_column(Integer, default=0)
    steps: Mapped[list] = mapped_column(JSON, default=list)


class ShoppingItem(ApiMixin, Base):
    __tablename__ = "shopping_items"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    item: Mapped[str] = mapped_column(String(120))
    need: Mapped[bool] = mapped_column(Boolean, default=True)
    stocked: Mapped[bool] = mapped_column(Boolean, default=False)
    note: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    added_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    got_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class RecurringRule(ApiMixin, Base):
    __tablename__ = "recurring_rules"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(120))
    rule: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    freq: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    short: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    sort: Mapped[float] = mapped_column(Float, default=0)


class Change(ApiMixin, Base):
    """Append-only log of what the person changed. Read back later to re-plan."""

    __tablename__ = "changes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    at: Mapped[datetime] = mapped_column(DateTime, default=now, index=True)
    type: Mapped[str] = mapped_column(String(24))
    task_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    project_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    from_: Mapped[Optional[dict]] = mapped_column("from", JSON, nullable=True)
    to: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extra: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    def to_api(self) -> dict[str, Any]:
        out = super().to_api()
        out["from"] = out.pop("from_", None)
        return out


class Note(ApiMixin, Base):
    """Free-text feedback from the person, read and answered later by an assistant."""

    __tablename__ = "notes"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    at: Mapped[datetime] = mapped_column(DateTime, default=now, index=True)
    text: Mapped[str] = mapped_column(Text)
    task_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    task_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="new")
    reply: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    replied_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class TrophyDef(ApiMixin, Base):
    """A trophy and the rule that earns it, e.g. {"type": "habit_streak", "habit": "walk"}."""

    __tablename__ = "trophy_defs"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    desc: Mapped[str] = mapped_column(String(255))
    goal: Mapped[int] = mapped_column(Integer, default=1)
    rule: Mapped[dict] = mapped_column(JSON)
    sort: Mapped[int] = mapped_column(Integer, default=0)


class TrophyAward(ApiMixin, Base):
    __tablename__ = "trophy_awards"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    earned_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Recap(ApiMixin, Base):
    __tablename__ = "recaps"
    week_start: Mapped[str] = mapped_column(String(10), primary_key=True)
    at: Mapped[datetime] = mapped_column(DateTime, default=now)
    data: Mapped[dict] = mapped_column(JSON, default=dict)


class Setting(ApiMixin, Base):
    """Key/value page settings: meal times, evening options, capacity, wording."""

    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[Any] = mapped_column(JSON)
