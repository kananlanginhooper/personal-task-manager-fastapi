from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import DbSession
from app.schemas.log import ChangeIn, ChangeOut, NoteIn, NoteOut, NotePatch
from app.services import log as service

router = APIRouter(tags=["log"])


@router.get("/changes", response_model=list[ChangeOut])
def list_changes(db: DbSession, limit: int = 100):
    return service.list_changes(db, limit)


@router.post("/changes", response_model=ChangeOut, status_code=201)
def add_change(body: ChangeIn, db: DbSession):
    return service.add_change(db, body)


@router.get("/notes", response_model=list[NoteOut])
def list_notes(db: DbSession, status: str | None = None):
    return service.list_notes(db, status)


@router.post("/notes", response_model=NoteOut, status_code=201)
def add_note(body: NoteIn, db: DbSession):
    return service.add_note(db, body)


@router.patch("/notes/{note_id}", response_model=NoteOut)
def patch_note(note_id: str, body: NotePatch, db: DbSession):
    return service.patch_note(db, note_id, body)
