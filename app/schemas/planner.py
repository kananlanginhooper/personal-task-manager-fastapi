"""Read-mostly planner content: areas, habits, goals (projects), recurring rules, trophies, shopping."""

from __future__ import annotations

from typing import Any

from app.schemas.base import CamelModel, UtcDatetime


class AreaOut(CamelModel):
    id: str
    name: str
    color: str
    note: str | None
    sort: int


class HabitOut(CamelModel):
    id: str
    group_name: str
    name: str
    sub: str | None
    cheer: str | None
    big: bool
    hype: str | None
    sort: int
    active: bool


class HabitMarkIn(CamelModel):
    habit: str
    done: bool


class HabitDayOut(CamelModel):
    date: str
    marks: dict[str, Any]


class ProjectOut(CamelModel):
    id: str
    area: str | None
    title: str
    prio: str
    est: str | None
    due: str | None
    next: str | None
    source: str | None
    sort: int
    steps: list[dict[str, Any]]


class RecurringOut(CamelModel):
    id: str
    title: str
    rule: str | None
    freq: str | None
    short: str | None
    sort: float


class TrophyOut(CamelModel):
    id: str
    name: str
    desc: str
    goal: int
    rule: dict[str, Any]
    sort: int


class AwardIn(CamelModel):
    id: str
    name: str | None = None


class AwardOut(CamelModel):
    id: str
    name: str | None
    earned_at: UtcDatetime


class ShoppingIn(CamelModel):
    item: str
    note: str | None = None


class ShoppingPatch(CamelModel):
    need: bool


class ShoppingOut(CamelModel):
    id: str
    item: str
    need: bool
    stocked: bool
    note: str | None
    added_at: UtcDatetime
    got_at: UtcDatetime | None


class RecapOut(CamelModel):
    week_start: str
    at: UtcDatetime
    data: dict[str, Any]
