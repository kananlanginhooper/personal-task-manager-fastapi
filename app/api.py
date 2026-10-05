"""HTTP routes. Every change a person makes is also written to the `changes` log with its reason."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import get_session
from .models import (
    Area,
    Change,
    HabitDay,
    HabitDef,
    Note,
    Project,
    Recap,
    RecurringRule,
    Setting,
    ShoppingItem,
    Task,
    TrophyAward,
    TrophyDef,
    now,
)

router = APIRouter(prefix="/api")
DB = Depends(get_session)


def new_id() -> str:
    return uuid.uuid4().hex[:20]


def iso_now() -> str:
    return now().isoformat() + "Z"


def log(db: Session, type_: str, title: Optional[str] = None, **kw: Any) -> Change:
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


def get_or_404(db: Session, model: Any, key: str) -> Any:
    row = db.get(model, key)
    if row is None:
        raise HTTPException(404, f"{model.__name__} {key} not found")
    return row


def add_days(date: str, n: int) -> str:
    return (datetime.strptime(date, "%Y-%m-%d") + timedelta(days=n)).strftime("%Y-%m-%d")


# ---------------------------------------------------------------- bootstrap


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/bootstrap")
def bootstrap(db: Session = DB) -> dict[str, Any]:
    """Everything the page needs to draw itself, in one call."""

    def rows(model: Any, order: Any = None) -> list[dict[str, Any]]:
        stmt = select(model)
        if order is not None:
            stmt = stmt.order_by(order)
        return [r.to_api() for r in db.scalars(stmt)]

    return {
        "settings": {s.key: s.value for s in db.scalars(select(Setting))},
        "areas": rows(Area, Area.sort),
        "habits": [h for h in rows(HabitDef, HabitDef.sort) if h["active"]],
        "habitDays": {d.date: d.marks for d in db.scalars(select(HabitDay))},
        "tasks": rows(Task, Task.date),
        "projects": rows(Project, Project.sort),
        "shopping": rows(ShoppingItem),
        "recurring": rows(RecurringRule, RecurringRule.sort),
        "trophies": rows(TrophyDef, TrophyDef.sort),
        "awards": {a.id: a.to_api() for a in db.scalars(select(TrophyAward))},
        "changes": [c.to_api() for c in db.scalars(select(Change).order_by(Change.id.desc()).limit(80))],
        "notes": [n.to_api() for n in db.scalars(select(Note).order_by(Note.at.desc()).limit(50))],
    }


# ---------------------------------------------------------------- tasks


class TaskIn(BaseModel):
    title: str
    date: str
    start: Optional[str] = None
    est: int = Field(15, ge=1)
    area: Optional[str] = None
    note: Optional[str] = None


class DoneIn(BaseModel):
    done: bool


class MoveIn(BaseModel):
    date: str
    start: Optional[str] = None
    type: str = "move"
    reason: Optional[str] = None


class EstimateIn(BaseModel):
    est: int = Field(..., ge=1)
    reason: Optional[str] = None


class ReasonIn(BaseModel):
    reason: Optional[str] = None


class TaskPatch(BaseModel):
    title: Optional[str] = None
    area: Optional[str] = None


@router.get("/tasks")
def list_tasks(start: Optional[str] = None, end: Optional[str] = None, db: Session = DB) -> list[dict[str, Any]]:
    stmt = select(Task).order_by(Task.date, Task.start)
    if start:
        stmt = stmt.where(Task.date >= start)
    if end:
        stmt = stmt.where(Task.date <= end)
    return [t.to_api() for t in db.scalars(stmt)]


@router.post("/tasks", status_code=201)
def create_task(body: TaskIn, db: Session = DB) -> dict[str, Any]:
    task = Task(id=new_id(), title=body.title, date=body.date, start=body.start, est=body.est, orig_est=body.est, area=body.area, note=body.note)
    db.add(task)
    log(db, "add", task.title, task_id=task.id, to={"date": task.date, "start": task.start, "est": task.est})
    db.commit()
    return task.to_api()


@router.patch("/tasks/{task_id}")
def patch_task(task_id: str, body: TaskPatch, db: Session = DB) -> dict[str, Any]:
    task = get_or_404(db, Task, task_id)
    changes = body.model_dump(exclude_none=True)
    if changes:
        before = {k: getattr(task, k) for k in changes}
        task.apply(changes)
        log(db, "edit", task.title, task_id=task.id, from_=before, to=changes)
        db.commit()
    return task.to_api()


@router.post("/tasks/{task_id}/done")
def set_done(task_id: str, body: DoneIn, db: Session = DB) -> dict[str, Any]:
    task = get_or_404(db, Task, task_id)
    task.done = body.done
    task.done_at = iso_now() if body.done else None
    log(db, "done" if body.done else "undone", task.title, task_id=task.id)
    db.commit()
    return task.to_api()


@router.post("/tasks/{task_id}/steps/{index}")
def set_task_step(task_id: str, index: int, body: DoneIn, db: Session = DB) -> dict[str, Any]:
    task = get_or_404(db, Task, task_id)
    steps = [dict(s) for s in (task.steps or [])]
    if not 0 <= index < len(steps):
        raise HTTPException(400, "No such step")
    steps[index]["done"] = body.done
    task.steps = steps
    if steps and all(s.get("done") for s in steps):
        task.done, task.done_at = True, iso_now()
    log(db, "step" if body.done else "unstep", f"{task.title}: {steps[index].get('t')}", task_id=task.id, extra={"index": index})
    db.commit()
    return task.to_api()


@router.post("/tasks/{task_id}/move")
def move_task(task_id: str, body: MoveIn, db: Session = DB) -> dict[str, Any]:
    task = get_or_404(db, Task, task_id)
    before = {"date": task.date, "start": task.start}
    after = {"date": body.date, "start": body.start}
    if before == after:
        return task.to_api()
    task.date, task.start = body.date, body.start
    task.moves = [*(task.moves or []), {"at": iso_now(), "from": before, "to": after, "type": body.type}]
    log(db, body.type, task.title, task_id=task.id, from_=before, to=after, reason=body.reason)
    db.commit()
    return task.to_api()


@router.post("/tasks/{task_id}/estimate")
def change_estimate(task_id: str, body: EstimateIn, db: Session = DB) -> dict[str, Any]:
    """Records the person's own estimate next to the original. The original is never overwritten."""
    task = get_or_404(db, Task, task_id)
    if body.est == task.est:
        return task.to_api()
    if task.orig_est is None:
        task.orig_est = task.est
    task.est_history = [*(task.est_history or []), {"at": iso_now(), "from": task.est, "to": body.est, "reason": body.reason}]
    log(db, "estimate", task.title, task_id=task.id, from_={"est": task.est}, to={"est": body.est}, reason=body.reason)
    task.est = body.est
    db.commit()
    return task.to_api()


@router.post("/tasks/{task_id}/split")
def split_task(task_id: str, body: ReasonIn, db: Session = DB) -> list[dict[str, Any]]:
    task = get_or_404(db, Task, task_id)
    base = task.title.removesuffix(" (part 1)").removesuffix(" (part 2)")
    half = max(5, round(task.est / 2 / 5) * 5)
    second = Task(id=new_id())
    for key, value in task.to_api().items():
        if key not in {"id", "createdAt", "updatedAt"}:
            second.apply({key: value})
    second.title, second.est, second.orig_est = f"{base} (part 2)", max(5, task.est - half), task.orig_est or task.est
    second.done, second.start, second.moves, second.split_from = False, None, [], task.id
    second.date = add_days(task.date, 1)
    task.orig_est = task.orig_est or task.est
    task.title, task.est = f"{base} (part 1)", half
    db.add(second)
    log(db, "split", base, task_id=task.id, from_={"est": task.orig_est}, to={"est": [task.est, second.est]}, reason=body.reason, extra={"newTaskId": second.id})
    db.commit()
    return [task.to_api(), second.to_api()]


@router.post("/tasks/{task_id}/skip")
def skip_task(task_id: str, body: ReasonIn, db: Session = DB) -> dict[str, Any]:
    task = get_or_404(db, Task, task_id)
    task.status = "skipped"
    log(db, "skip", task.title, task_id=task.id, reason=body.reason)
    db.commit()
    return task.to_api()


# ---------------------------------------------------------------- projects


@router.post("/projects/{project_id}/steps/{index}")
def set_project_step(project_id: str, index: int, body: DoneIn, db: Session = DB) -> dict[str, Any]:
    project = get_or_404(db, Project, project_id)
    steps = [dict(s) for s in (project.steps or [])]
    if not 0 <= index < len(steps):
        raise HTTPException(400, "No such step")
    steps[index]["done"] = body.done
    project.steps = steps
    log(db, "step" if body.done else "unstep", f"{project.title}: {steps[index].get('t')}", project_id=project.id, extra={"index": index, "source": project.source})
    db.commit()
    return project.to_api()


# ---------------------------------------------------------------- habits


class HabitMarkIn(BaseModel):
    habit: str
    done: bool


@router.put("/habits/{date}")
def mark_habit(date: str, body: HabitMarkIn, db: Session = DB) -> dict[str, Any]:
    day = db.get(HabitDay, date) or HabitDay(date=date, marks={})
    day.marks = {**(day.marks or {}), body.habit: body.done}
    db.merge(day)
    if body.done:
        habit = db.get(HabitDef, body.habit)
        log(db, "habit", habit.name if habit else body.habit, extra={"habit": body.habit, "date": date})
    db.commit()
    return {"date": date, "marks": day.marks}


# ---------------------------------------------------------------- shopping


class ShoppingIn(BaseModel):
    item: str
    note: Optional[str] = None


class ShoppingPatch(BaseModel):
    need: bool


@router.post("/shopping", status_code=201)
def add_shopping(body: ShoppingIn, db: Session = DB) -> dict[str, Any]:
    row = ShoppingItem(id=new_id(), item=body.item, note=body.note, need=True)
    db.add(row)
    log(db, "shop", f"Added {body.item}")
    db.commit()
    return row.to_api()


@router.patch("/shopping/{item_id}")
def patch_shopping(item_id: str, body: ShoppingPatch, db: Session = DB) -> dict[str, Any]:
    row = get_or_404(db, ShoppingItem, item_id)
    row.need = body.need
    row.got_at = None if body.need else now()
    db.commit()
    return row.to_api()


# ---------------------------------------------------------------- log, notes, trophies, recaps


class ChangeIn(BaseModel):
    type: str
    title: Optional[str] = None
    reason: Optional[str] = None
    extra: Optional[dict[str, Any]] = None


@router.get("/changes")
def list_changes(limit: int = 100, db: Session = DB) -> list[dict[str, Any]]:
    return [c.to_api() for c in db.scalars(select(Change).order_by(Change.id.desc()).limit(min(limit, 1000)))]


@router.post("/changes", status_code=201)
def add_change(body: ChangeIn, db: Session = DB) -> dict[str, Any]:
    """For moments only the page sees, like picking an evening alternative."""
    entry = log(db, body.type, body.title, reason=body.reason, extra=body.extra)
    db.commit()
    return entry.to_api()


class NoteIn(BaseModel):
    text: str = Field(..., min_length=1)
    taskId: Optional[str] = None


class NotePatch(BaseModel):
    status: Optional[str] = None
    reply: Optional[str] = None


@router.get("/notes")
def list_notes(status: Optional[str] = None, db: Session = DB) -> list[dict[str, Any]]:
    stmt = select(Note).order_by(Note.at.desc())
    if status:
        stmt = stmt.where(Note.status == status)
    return [n.to_api() for n in db.scalars(stmt)]


@router.post("/notes", status_code=201)
def add_note(body: NoteIn, db: Session = DB) -> dict[str, Any]:
    task = db.get(Task, body.taskId) if body.taskId else None
    note = Note(id=new_id(), text=body.text.strip(), task_id=body.taskId, task_title=task.title if task else None)
    db.add(note)
    db.commit()
    return note.to_api()


@router.patch("/notes/{note_id}")
def patch_note(note_id: str, body: NotePatch, db: Session = DB) -> dict[str, Any]:
    note = get_or_404(db, Note, note_id)
    if body.status:
        note.status = body.status
    if body.reply is not None:
        note.reply, note.replied_at = body.reply, now()
    db.commit()
    return note.to_api()


class AwardIn(BaseModel):
    id: str
    name: Optional[str] = None


@router.post("/trophies/awards", status_code=201)
def award(body: AwardIn, db: Session = DB) -> dict[str, Any]:
    existing = db.get(TrophyAward, body.id)
    if existing:
        return existing.to_api()
    row = TrophyAward(id=body.id, name=body.name)
    db.add(row)
    log(db, "trophy", f"Trophy: {body.name or body.id}")
    db.commit()
    return row.to_api()


@router.put("/recaps/{week_start}")
def save_recap(week_start: str, body: dict[str, Any], db: Session = DB) -> dict[str, Any]:
    row = db.merge(Recap(week_start=week_start, at=now(), data=body))
    db.commit()
    return row.to_api()
