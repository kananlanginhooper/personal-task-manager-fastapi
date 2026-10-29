"""Goals (projects), habits, shopping, trophies and weekly recaps."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.db.models import HabitDay, HabitDef, Project, Recap, ShoppingItem, TrophyAward, now
from app.schemas.planner import AwardIn, ShoppingIn
from app.services.common import InvalidRequestError, get_or_404, log, new_id


def set_project_step(db: Session, project_id: str, index: int, done: bool) -> Project:
    project = get_or_404(db, Project, project_id)
    steps = [dict(s) for s in (project.steps or [])]
    if not 0 <= index < len(steps):
        raise InvalidRequestError("No such step")
    steps[index]["done"] = done
    project.steps = steps
    log(
        db,
        "step" if done else "unstep",
        f"{project.title}: {steps[index].get('t')}",
        project_id=project.id,
        extra={"index": index, "source": project.source},
    )
    db.commit()
    return project


def mark_habit(db: Session, date: str, habit_id: str, done: bool) -> HabitDay:
    day = db.get(HabitDay, date) or HabitDay(date=date, marks={})
    day.marks = {**(day.marks or {}), habit_id: done}
    db.merge(day)
    if done:
        habit = db.get(HabitDef, habit_id)
        log(db, "habit", habit.name if habit else habit_id, extra={"habit": habit_id, "date": date})
    db.commit()
    return day


def add_shopping(db: Session, body: ShoppingIn) -> ShoppingItem:
    row = ShoppingItem(id=new_id(), item=body.item, note=body.note, need=True)
    db.add(row)
    log(db, "shop", f"Added {body.item}")
    db.commit()
    return row


def set_shopping_need(db: Session, item_id: str, need: bool) -> ShoppingItem:
    row = get_or_404(db, ShoppingItem, item_id)
    row.need = need
    row.got_at = None if need else now()
    db.commit()
    return row


def award(db: Session, body: AwardIn) -> TrophyAward:
    """Idempotent: awarding the same trophy twice returns the first award."""
    existing = db.get(TrophyAward, body.id)
    if existing:
        return existing
    row = TrophyAward(id=body.id, name=body.name)
    db.add(row)
    log(db, "trophy", f"Trophy: {body.name or body.id}")
    db.commit()
    return row


def save_recap(db: Session, week_start: str, data: dict[str, Any]) -> Recap:
    row = db.merge(Recap(week_start=week_start, at=now(), data=data))
    db.commit()
    return row
