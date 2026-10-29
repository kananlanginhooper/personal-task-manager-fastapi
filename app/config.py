"""Runtime settings, read from environment variables (see .env.example)."""
from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import URL


def _load_env_file() -> None:
    """Load KEY=VALUE lines from the file named by ENV_FILE (default: .env), without overriding real env vars."""
    path = Path(os.environ.get("ENV_FILE", ".env"))
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


_load_env_file()

def _database_url() -> str:
    """DATABASE_URL wins; otherwise build a MySQL URL from DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD; else local SQLite."""
    if os.environ.get("DATABASE_URL"):
        return os.environ["DATABASE_URL"]
    host = os.environ.get("DB_HOST", "")
    if not host:
        return "sqlite:///./local.db"
    return URL.create(
        "mysql+pymysql",
        username=os.environ.get("DB_USER", "gameplan"),
        password=os.environ.get("DB_PASSWORD", ""),
        host=host,
        port=int(os.environ.get("DB_PORT", "3306")),
        database=os.environ.get("DB_NAME", "gameplan"),
    ).render_as_string(hide_password=False)


DATABASE_URL: str = _database_url()
CORS_ORIGINS: list[str] = [o.strip() for o in os.environ.get("CORS_ORIGINS", "http://localhost:4200").split(",") if o.strip()]
# Optional shared token. When set, every /api call must send `Authorization: Bearer <token>`.
API_TOKEN: str = os.environ.get("API_TOKEN", "")

# Where the app lives and who may frame it: config only, so it runs unchanged on http://<ip>:<port> or https://<app>.<domain>.
# UI_BASE_PATH: path prefix the app is served under ("/" by default); index.html gets it as <base href> at request time,
# and requests under it are routed as if at the root, so one build works under any path.
_base = os.environ.get("UI_BASE_PATH", "/").strip("/")
UI_BASE: str = f"/{_base}/" if _base else "/"
PUBLIC_URL: str = os.environ.get("PUBLIC_URL", "")                    # empty = wherever it's opened
FRAME_ANCESTORS: list[str] = os.environ.get("FRAME_ANCESTORS", "").split()  # wrapper origins allowed to show it in an iframe
LOGIN: bool = os.environ.get("LOGIN", "off") == "on"                  # OIDC login isn't built yet; the switch is here for the UI
OIDC_ISSUER: str = os.environ.get("OIDC_ISSUER", "")
OIDC_CLIENT_ID: str = os.environ.get("OIDC_CLIENT_ID", "")
# Built Angular UI (personal-task-manager-angular). The Docker image builds it in; without it, only the API is served.
UI_DIR: Path = Path(os.environ.get("UI_DIR", "ui"))
