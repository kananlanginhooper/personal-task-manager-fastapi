from __future__ import annotations

from typing import Any

from pydantic import Field

from app.schemas.base import CamelModel, UtcDatetime


class TaskOut(CamelModel):
    id: str
    title: str
    date: str
    start: str | None
    est: int
    orig_est: int | None
    travel: int
    close_by: str | None
    leave: str | None
    area: str | None
    kind: str | None
    note: str | None
    cheer: str | None
    hype: str | None
    cost: int | None
    locked: bool
    recurring: bool
    remind: bool
    work: bool
    big: bool
    dread: bool
    done: bool
    done_at: str | None
    status: str | None
    steps: list[dict[str, Any]] | None
    est_history: list[dict[str, Any]] | None
    moves: list[dict[str, Any]] | None
    split_from: str | None
    created_at: UtcDatetime
    updated_at: UtcDatetime


class TaskIn(CamelModel):
    title: str
    date: str
    start: str | None = None
    est: int = Field(15, ge=1)
    area: str | None = None
    note: str | None = None


class TaskPatch(CamelModel):
    title: str | None = None
    area: str | None = None


class MoveIn(CamelModel):
    date: str
    start: str | None = None
    type: str = "move"
    reason: str | None = None


class EstimateIn(CamelModel):
    est: int = Field(..., ge=1)
    reason: str | None = None
