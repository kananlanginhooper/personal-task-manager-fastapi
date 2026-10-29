"""The change log and the notes left for an assistant."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from app.schemas.base import CamelModel, UtcDatetime


class ChangeOut(CamelModel):
    id: int
    at: UtcDatetime
    type: str
    task_id: str | None
    project_id: str | None
    title: str | None
    to: dict[str, Any] | None
    reason: str | None
    extra: dict[str, Any] | None
    # "from" is a Python keyword; the column attribute is from_. Last, as the API has always sent it.
    from_: dict[str, Any] | None = Field(alias="from")


class ChangeIn(CamelModel):
    type: str
    title: str | None = None
    reason: str | None = None
    extra: dict[str, Any] | None = None


class NoteOut(CamelModel):
    id: str
    at: UtcDatetime
    text: str
    task_id: str | None
    task_title: str | None
    status: str
    reply: str | None
    replied_at: UtcDatetime | None


class NoteIn(CamelModel):
    text: str = Field(..., min_length=1)
    task_id: str | None = None


class NotePatch(CamelModel):
    status: str | None = None
    reply: str | None = None
