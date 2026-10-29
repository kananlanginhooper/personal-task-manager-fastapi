"""Tasks. Every change is logged with its reason, and the original estimate is never overwritten."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Task
from app.schemas.tasks import EstimateIn, MoveIn, TaskIn, TaskPatch
from app.services.common import InvalidRequestError, add_days, get_or_404, iso_now, log, new_id


def list_tasks(db: Session, start: str | None, end: str | None) -> list[Task]:
    stmt = select(Task).order_by(Task.date, Task.start)
    if start:
        stmt = stmt.where(Task.date >= start)
    if end:
        stmt = stmt.where(Task.date <= end)
    return list(db.scalars(stmt))


def create_task(db: Session, body: TaskIn) -> Task:
    task = Task(
        id=new_id(),
        title=body.title,
        date=body.date,
        start=body.start,
        est=body.est,
        orig_est=body.est,
        area=body.area,
        note=body.note,
    )
    db.add(task)
    log(db, "add", task.title, task_id=task.id, to={"date": task.date, "start": task.start, "est": task.est})
    db.commit()
    return task


def patch_task(db: Session, task_id: str, body: TaskPatch) -> Task:
    task = get_or_404(db, Task, task_id)
    changes = body.model_dump(exclude_none=True)
    if changes:
        before = {k: getattr(task, k) for k in changes}
        task.apply(changes)
        log(db, "edit", task.title, task_id=task.id, from_=before, to=changes)
        db.commit()
    return task


def set_done(db: Session, task_id: str, done: bool) -> Task:
    task = get_or_404(db, Task, task_id)
    task.done = done
    task.done_at = iso_now() if done else None
    log(db, "done" if done else "undone", task.title, task_id=task.id)
    db.commit()
    return task


def set_step(db: Session, task_id: str, index: int, done: bool) -> Task:
    """Check one step; checking the last open step finishes the task."""
    task = get_or_404(db, Task, task_id)
    steps = [dict(s) for s in (task.steps or [])]
    if not 0 <= index < len(steps):
        raise InvalidRequestError("No such step")
    steps[index]["done"] = done
    task.steps = steps
    if steps and all(s.get("done") for s in steps):
        task.done, task.done_at = True, iso_now()
    log(db, "step" if done else "unstep", f"{task.title}: {steps[index].get('t')}", task_id=task.id, extra={"index": index})
    db.commit()
    return task


def move_task(db: Session, task_id: str, body: MoveIn) -> Task:
    task = get_or_404(db, Task, task_id)
    before = {"date": task.date, "start": task.start}
    after = {"date": body.date, "start": body.start}
    if before == after:
        return task
    task.date, task.start = body.date, body.start
    task.moves = [*(task.moves or []), {"at": iso_now(), "from": before, "to": after, "type": body.type}]
    log(db, body.type, task.title, task_id=task.id, from_=before, to=after, reason=body.reason)
    db.commit()
    return task


def change_estimate(db: Session, task_id: str, body: EstimateIn) -> Task:
    """Record the person's own estimate next to the original."""
    task = get_or_404(db, Task, task_id)
    if body.est == task.est:
        return task
    if task.orig_est is None:
        task.orig_est = task.est
    task.est_history = [*(task.est_history or []), {"at": iso_now(), "from": task.est, "to": body.est, "reason": body.reason}]
    log(db, "estimate", task.title, task_id=task.id, from_={"est": task.est}, to={"est": body.est}, reason=body.reason)
    task.est = body.est
    db.commit()
    return task


def split_task(db: Session, task_id: str, reason: str | None) -> list[Task]:
    """Halve a task: part 1 stays, part 2 goes to the next day. Both keep the original estimate."""
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
    log(
        db,
        "split",
        base,
        task_id=task.id,
        from_={"est": task.orig_est},
        to={"est": [task.est, second.est]},
        reason=reason,
        extra={"newTaskId": second.id},
    )
    db.commit()
    return [task, second]


def skip_task(db: Session, task_id: str, reason: str | None) -> Task:
    task = get_or_404(db, Task, task_id)
    task.status = "skipped"
    log(db, "skip", task.title, task_id=task.id, reason=reason)
    db.commit()
    return task
