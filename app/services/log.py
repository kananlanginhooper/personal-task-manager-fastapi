"""The change log, notes for an assistant, and the one-call bootstrap."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import (
    Area,
    Change,
    HabitDay,
    HabitDef,
    Note,
    Project,
    RecurringRule,
    Setting,
    ShoppingItem,
    Task,
    TrophyAward,
    TrophyDef,
    now,
)
from app.schemas.log import ChangeIn, NoteIn, NotePatch
from app.services.common import get_or_404, log, new_id


def bootstrap(db: Session) -> dict[str, Any]:
    """Everything the page needs to draw itself, in one call."""
    return {
        "settings": {s.key: s.value for s in db.scalars(select(Setting))},
        "areas": list(db.scalars(select(Area).order_by(Area.sort))),
        "habits": [h for h in db.scalars(select(HabitDef).order_by(HabitDef.sort)) if h.active],
        "habitDays": {d.date: d.marks for d in db.scalars(select(HabitDay))},
        "tasks": list(db.scalars(select(Task).order_by(Task.date))),
        "projects": list(db.scalars(select(Project).order_by(Project.sort))),
        "shopping": list(db.scalars(select(ShoppingItem))),
        "recurring": list(db.scalars(select(RecurringRule).order_by(RecurringRule.sort))),
        "trophies": list(db.scalars(select(TrophyDef).order_by(TrophyDef.sort))),
        "awards": {a.id: a for a in db.scalars(select(TrophyAward))},
        "changes": list_changes(db, 80),
        "notes": list(db.scalars(select(Note).order_by(Note.at.desc()).limit(50))),
    }


def list_changes(db: Session, limit: int) -> list[Change]:
    return list(db.scalars(select(Change).order_by(Change.id.desc()).limit(min(limit, 1000))))


def add_change(db: Session, body: ChangeIn) -> Change:
    """For moments only the page sees, like picking an evening alternative."""
    entry = log(db, body.type, body.title, reason=body.reason, extra=body.extra)
    db.commit()
    return entry


def list_notes(db: Session, status: str | None) -> list[Note]:
    stmt = select(Note).order_by(Note.at.desc())
    if status:
        stmt = stmt.where(Note.status == status)
    return list(db.scalars(stmt))


def add_note(db: Session, body: NoteIn) -> Note:
    task = db.get(Task, body.task_id) if body.task_id else None
    note = Note(id=new_id(), text=body.text.strip(), task_id=body.task_id, task_title=task.title if task else None)
    db.add(note)
    db.commit()
    return note


def patch_note(db: Session, note_id: str, body: NotePatch) -> Note:
    note = get_or_404(db, Note, note_id)
    if body.status:
        note.status = body.status
    if body.reply is not None:
        note.reply, note.replied_at = body.reply, now()
    db.commit()
    return note
