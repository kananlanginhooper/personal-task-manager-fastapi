from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from app.schemas.base import CamelModel
from app.schemas.log import ChangeOut, NoteOut
from app.schemas.planner import AreaOut, AwardOut, HabitOut, ProjectOut, RecurringOut, ShoppingOut, TrophyOut
from app.schemas.tasks import TaskOut


class HealthOut(BaseModel):
    status: str


class LoginConfig(CamelModel):
    enabled: bool
    issuer: str
    client_id: str


class RuntimeConfig(CamelModel):
    """GET /api/config: what the UI needs before it starts (group-standard shape)."""

    api_base: str
    base_path: str
    public_url: str
    frame_parents: list[str]
    login: LoginConfig


class BootstrapOut(BaseModel):
    """Everything the page needs to draw itself, in one call. Keys are already camelCase."""

    settings: dict[str, Any]
    areas: list[AreaOut]
    habits: list[HabitOut]
    habitDays: dict[str, dict[str, Any]]
    tasks: list[TaskOut]
    projects: list[ProjectOut]
    shopping: list[ShoppingOut]
    recurring: list[RecurringOut]
    trophies: list[TrophyOut]
    awards: dict[str, AwardOut]
    changes: list[ChangeOut]
    notes: list[NoteOut]
