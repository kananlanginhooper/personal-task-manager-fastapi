from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.api.deps import DbSession
from app.schemas.base import DoneIn
from app.schemas.planner import (
    AwardIn,
    AwardOut,
    HabitDayOut,
    HabitMarkIn,
    ProjectOut,
    RecapOut,
    ShoppingIn,
    ShoppingOut,
    ShoppingPatch,
)
from app.services import planner as service

router = APIRouter(tags=["planner"])


@router.post("/projects/{project_id}/steps/{index}", response_model=ProjectOut)
def set_project_step(project_id: str, index: int, body: DoneIn, db: DbSession):
    return service.set_project_step(db, project_id, index, body.done)


@router.put("/habits/{date}", response_model=HabitDayOut)
def mark_habit(date: str, body: HabitMarkIn, db: DbSession):
    return service.mark_habit(db, date, body.habit, body.done)


@router.post("/shopping", response_model=ShoppingOut, status_code=201)
def add_shopping(body: ShoppingIn, db: DbSession):
    return service.add_shopping(db, body)


@router.patch("/shopping/{item_id}", response_model=ShoppingOut)
def patch_shopping(item_id: str, body: ShoppingPatch, db: DbSession):
    return service.set_shopping_need(db, item_id, body.need)


@router.post("/trophies/awards", response_model=AwardOut, status_code=201)
def award(body: AwardIn, db: DbSession):
    return service.award(db, body)


@router.put("/recaps/{week_start}", response_model=RecapOut)
def save_recap(week_start: str, body: dict[str, Any], db: DbSession):
    return service.save_recap(db, week_start, body)
