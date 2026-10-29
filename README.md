# personal-task-manager-fastapi

The API behind a personal planning dashboard: a daily plan, a drag-and-drop week, habits with streaks, goals broken into small steps, a shopping list, trophies, a Sunday recap, and notes you leave for an assistant to read later.

The front end lives in [personal-task-manager-angular](https://github.com/kananlanginhooper/personal-task-manager-angular), which also has a demo you can click through on GitHub Pages.

## Design rules

- **Code only.** Areas of life, habits, task lists, trophies and all wording live in the database. Nothing personal is in this repository.
- **Never overwrite what the person said.** Moving a task, changing an estimate, splitting or dropping one adds an entry to the `changes` log with the reason. The original estimate is kept next to the new one.
- **Notes for later.** `notes` holds free-text feedback with a `status` (`new` / `read`) and a `reply`, so an assistant can process it and answer.

## Run it

```bash
git clone https://github.com/kananlanginhooper/personal-task-manager-angular ../personal-task-manager-angular
cp .env.example .env        # set DB_HOST, DB_USER, DB_PASSWORD (MySQL 8)
docker compose up -d --build
```

The image builds the Angular UI from the sibling clone and serves it with the API, so `http://localhost:8095/` is the whole app. The compose file has no database service: the API connects to an existing MySQL server at `DB_HOST`.

Nothing about hosts, ports or paths is compiled in. `GET /api/config` gives the UI its runtime settings, and these `.env` values move the app from `http://<host>:<port>` to `https://<app>.<domain>`:

| Variable | What it does |
|---|---|
| `PUBLIC_URL` | The app's public address |
| `UI_BASE_PATH` | Path prefix to serve under (`/` by default); set as `<base href>` at request time |
| `FRAME_ANCESTORS` | Origins allowed to show the app in an iframe (sent as CSP `frame-ancestors 'self' ...`) |
| `FORWARDED_ALLOW_IPS` | Reverse proxies whose `X-Forwarded-*` headers are trusted |
| `LOGIN`, `OIDC_ISSUER`, `OIDC_CLIENT_ID` | OpenID Connect login switch (not built yet) |

Without Docker (API only):

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --port 8095
```

With no `DB_HOST` or `DATABASE_URL` set, it falls back to a local SQLite file. Tables are created on first start. Load your own content from a JSON file kept outside the repo:

```bash
docker compose run --rm -v /path/to/private:/private:ro api python -m scripts.import_seed /private/seed.json
```

API docs are served at `/docs` once it's running. Every route declares its response model, so `/openapi.json` is complete; the Angular app generates its TypeScript types from it.

## Code layout

```
app/
  main.py              create_app(): routers, middleware (frame-ancestors, base path, token), the built UI
  core/config.py       Settings (pydantic-settings): the only place env and .env are read
  api/routes/*.py      thin routers: validate, call a service, return a schema
  schemas/*.py         Pydantic request/response models (camelCase on the wire)
  services/*.py        the logic; no HTTP objects
  db/                  SQLAlchemy engine, session and tables
migrations/            Alembic
```

## Database migrations

Tables are created on first start if they're missing. Schema changes go through Alembic:

```bash
alembic upgrade head                                  # once per database; the baseline only records the revision on an existing one
alembic revision --autogenerate -m "what changed"     # after editing app/db/models.py
```

## Tests

```bash
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest
ruff check . && ruff format --check .
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
