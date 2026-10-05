"""Runtime settings, read from environment variables (see .env.example)."""
from __future__ import annotations

import os
from pathlib import Path


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

DATABASE_URL: str = os.environ.get("DATABASE_URL", "sqlite:///./local.db")
CORS_ORIGINS: list[str] = [o.strip() for o in os.environ.get("CORS_ORIGINS", "http://localhost:4200").split(",") if o.strip()]
# Optional shared token. When set, every /api call must send `Authorization: Bearer <token>`.
API_TOKEN: str = os.environ.get("API_TOKEN", "")
