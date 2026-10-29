from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import DbSession
from app.core.config import settings
from app.schemas.system import BootstrapOut, HealthOut, LoginConfig, RuntimeConfig
from app.services import log as log_service

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthOut)
def health():
    return {"status": "ok"}


@router.get("/config", response_model=RuntimeConfig)
def runtime_config():
    """The UI's runtime config, loaded before it starts: nothing about hosts, ports or paths is compiled into it."""
    return RuntimeConfig(
        api_base=settings.ui_base + "api/",
        base_path=settings.ui_base,
        public_url=settings.public_url,
        frame_parents=settings.frame_ancestor_list,
        login=LoginConfig(enabled=settings.login_enabled, issuer=settings.oidc_issuer, client_id=settings.oidc_client_id),
    )


@router.get("/bootstrap", response_model=BootstrapOut)
def bootstrap(db: DbSession):
    return log_service.bootstrap(db)
