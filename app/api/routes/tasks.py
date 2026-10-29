from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import DbSession
from app.schemas.base import DoneIn, ReasonIn
from app.schemas.tasks import EstimateIn, MoveIn, TaskIn, TaskOut, TaskPatch
from app.services import tasks as service

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskOut])
def list_tasks(db: DbSession, start: str | None = None, end: str | None = None):
    return service.list_tasks(db, start, end)


@router.post("", response_model=TaskOut, status_code=201)
def create_task(body: TaskIn, db: DbSession):
    return service.create_task(db, body)


@router.patch("/{task_id}", response_model=TaskOut)
def patch_task(task_id: str, body: TaskPatch, db: DbSession):
    return service.patch_task(db, task_id, body)


@router.post("/{task_id}/done", response_model=TaskOut)
def set_done(task_id: str, body: DoneIn, db: DbSession):
    return service.set_done(db, task_id, body.done)


@router.post("/{task_id}/steps/{index}", response_model=TaskOut)
def set_step(task_id: str, index: int, body: DoneIn, db: DbSession):
    return service.set_step(db, task_id, index, body.done)


@router.post("/{task_id}/move", response_model=TaskOut)
def move_task(task_id: str, body: MoveIn, db: DbSession):
    return service.move_task(db, task_id, body)


@router.post("/{task_id}/estimate", response_model=TaskOut)
def change_estimate(task_id: str, body: EstimateIn, db: DbSession):
    return service.change_estimate(db, task_id, body)


@router.post("/{task_id}/split", response_model=list[TaskOut])
def split_task(task_id: str, body: ReasonIn, db: DbSession):
    return service.split_task(db, task_id, body.reason)


@router.post("/{task_id}/skip", response_model=TaskOut)
def skip_task(task_id: str, body: ReasonIn, db: DbSession):
    return service.skip_task(db, task_id, body.reason)
