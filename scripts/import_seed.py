"""Load a JSON seed file into the database (insert or update by id).

The seed file holds personal content, so keep it OUTSIDE this repository:

    python -m scripts.import_seed /path/to/private/seed.json

Top-level keys (all optional): settings {key: value}, areas, habits, trophies, tasks, projects,
shopping, recurring, notes, changes, awards (lists of objects with camelCase fields),
habitDays {YYYY-MM-DD: {habitId: bool}}.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from app.db import SessionLocal, create_all
from app.models import (
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
)

LISTS = {
    "areas": Area,
    "habits": HabitDef,
    "trophies": TrophyDef,
    "tasks": Task,
    "projects": Project,
    "shopping": ShoppingItem,
    "recurring": RecurringRule,
    "notes": Note,
    "awards": TrophyAward,
}
DATETIME_FIELDS = {"at", "addedAt", "gotAt", "earnedAt", "repliedAt", "createdAt", "updatedAt"}


def _clean(row: dict[str, Any]) -> dict[str, Any]:
    out = {}
    for key, value in row.items():
        if key in DATETIME_FIELDS and isinstance(value, str):
            value = datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
        out[key] = value
    return out


def main(path: str) -> None:
    seed = json.loads(Path(path).read_text(encoding="utf-8"))
    create_all()
    counts: dict[str, int] = {}
    with SessionLocal() as db:
        for key, value in (seed.get("settings") or {}).items():
            db.merge(Setting(key=key, value=value))
        counts["settings"] = len(seed.get("settings") or {})
        for name, model in LISTS.items():
            for row in seed.get(name) or []:
                obj = db.get(model, row["id"]) or model(id=row["id"])
                obj.apply(_clean(row))
                db.merge(obj)
            counts[name] = len(seed.get(name) or [])
        for date, marks in (seed.get("habitDays") or {}).items():
            db.merge(HabitDay(date=date, marks=marks))
        counts["habitDays"] = len(seed.get("habitDays") or {})
        if seed.get("changes") and not db.query(Change).count():
            for row in seed["changes"]:
                c = Change()
                row = _clean(row)
                row["from_"] = row.pop("from", None)
                for k, v in row.items():
                    if k == "from_":
                        c.from_ = v
                    else:
                        c.apply({k: v})
                db.add(c)
            counts["changes"] = len(seed["changes"])
        db.commit()
    print("Imported:", ", ".join(f"{k} {v}" for k, v in counts.items() if v))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python -m scripts.import_seed /path/to/seed.json")
    main(sys.argv[1])
