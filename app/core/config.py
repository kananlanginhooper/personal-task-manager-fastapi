"""Runtime settings. The only place environment variables (and the .env file) are read."""

from __future__ import annotations

import os
from functools import cached_property
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    # ENV_FILE picks another file (the old systemd unit uses it); real environment variables always win.
    model_config = SettingsConfigDict(env_file=os.environ.get("ENV_FILE", ".env"), extra="ignore")

    # Database: DATABASE_URL wins; otherwise a MySQL URL from DB_*; with neither, a local SQLite file.
    database_url: str = ""
    db_host: str = ""
    db_port: int = 3306
    db_name: str = "gameplan"
    db_user: str = "gameplan"
    db_password: str = ""

    cors_origins: str = "http://localhost:4200"  # comma-separated
    # Optional shared token. When set, every /api call except /api/config must send `Authorization: Bearer <token>`.
    api_token: str = ""

    # Where the app lives and who may frame it, so it runs unchanged on http://<ip>:<port> or https://<app>.<domain>.
    ui_base_path: str = "/"  # path prefix; index.html gets it as <base href> at request time
    public_url: str = ""  # empty = wherever it's opened
    frame_ancestors: str = ""  # space-separated wrapper origins allowed to show it in an iframe
    login: str = "off"  # OIDC login isn't built yet; the switch is here for the UI
    oidc_issuer: str = ""
    oidc_client_id: str = ""
    # Built Angular UI. The Docker image builds it in; without it, only the API is served.
    ui_dir: Path = Path("ui")

    @cached_property
    def sqlalchemy_url(self) -> str:
        if self.database_url:
            return self.database_url
        if not self.db_host:
            return "sqlite:///./local.db"
        return URL.create(
            "mysql+pymysql",
            username=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
        ).render_as_string(hide_password=False)

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def ui_base(self) -> str:
        base = self.ui_base_path.strip("/")
        return f"/{base}/" if base else "/"

    @property
    def frame_ancestor_list(self) -> list[str]:
        return self.frame_ancestors.split()

    @property
    def login_enabled(self) -> bool:
        return self.login == "on"


settings = Settings()
