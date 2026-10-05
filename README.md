# personal-task-manager-fastapi

The API behind a personal planning dashboard: a daily plan, a drag-and-drop week, habits with streaks, goals broken into small steps, a shopping list, trophies, a Sunday recap, and notes you leave for an assistant to read later.

The front end lives in [personal-task-manager-angular](https://github.com/kananlanginhooper/personal-task-manager-angular), which also has a demo you can click through on GitHub Pages.

## Design rules

- **Code only.** Areas of life, habits, task lists, trophies and all wording live in the database. Nothing personal is in this repository.
- **Never overwrite what the person said.** Moving a task, changing an estimate, splitting or dropping one adds an entry to the `changes` log with the reason. The original estimate is kept next to the new one.
- **Notes for later.** `notes` holds free-text feedback with a `status` (`new` / `read`) and a `reply`, so an assistant can process it and answer.

## Run it

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env        # set DATABASE_URL (MySQL 8 or SQLite)
.venv/bin/uvicorn app.main:app --port 8095
```

Tables are created on first start. Load your own content from a JSON file kept outside the repo:

```bash
.venv/bin/python -m scripts.import_seed /path/to/private/seed.json
```

API docs are served at `/docs` once it's running.

## Tests

```bash
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest
```

## Privacy check before every push

`tools/privacy_scan.py` searches every tracked file for terms in a private denylist (`~/.config/personal-task-manager/denylist.txt` or `$PRIVACY_DENYLIST`) and blocks the push on any match. Turn it on once per clone:

```bash
git config core.hooksPath .githooks
```

## Endpoints

| Method | Path | What it does |
|---|---|---|
| GET | `/api/bootstrap` | Everything the page needs in one call |
| POST | `/api/tasks` | Add a task |
| POST | `/api/tasks/{id}/move` | Move to a new day or time (logged) |
| POST | `/api/tasks/{id}/estimate` | Record your own estimate (logged, original kept) |
| POST | `/api/tasks/{id}/split` | Split into two halves |
| POST | `/api/tasks/{id}/done` | Check off or uncheck |
| POST | `/api/tasks/{id}/skip` | Drop it, with a reason |
| POST | `/api/projects/{id}/steps/{i}` | Check a goal step |
| PUT | `/api/habits/{date}` | Mark a habit for a day |
| GET/POST/PATCH | `/api/notes` | Notes for the assistant, with replies |
| GET | `/api/changes` | The change log |
| POST | `/api/trophies/awards` | Record an earned trophy |
| PUT | `/api/recaps/{weekStart}` | Save a weekly recap summary |

Set `API_TOKEN` to require `Authorization: Bearer <token>` until a real sign-in is in front of it.

## License

GPL-3.0
