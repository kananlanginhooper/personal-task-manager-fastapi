from __future__ import annotations

import html
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

from . import config
from .api import router
from .db import create_all


@asynccontextmanager
async def lifespan(_: FastAPI):  # type: ignore[no-untyped-def]
    create_all()
    yield


app = FastAPI(title="Personal Task Manager API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def require_token(request: Request, call_next):  # type: ignore[no-untyped-def]
    """Optional shared-token check until a real sign-in sits in front of the API. /api/config stays open: the UI needs it first."""
    path = request.url.path
    if config.API_TOKEN and path.startswith("/api") and path != "/api/config" and request.method != "OPTIONS":
        if request.headers.get("authorization") != f"Bearer {config.API_TOKEN}":
            return JSONResponse({"detail": "Sign-in required"}, status_code=401)
    return await call_next(request)


@app.middleware("http")
async def frame_policy(request: Request, call_next):  # type: ignore[no-untyped-def]
    """Only this app and the configured wrapper origins may show it in an iframe."""
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = "frame-ancestors " + " ".join(["'self'", *config.FRAME_ANCESTORS])
    return response


@app.middleware("http")
async def strip_base_path(request: Request, call_next):  # type: ignore[no-untyped-def]
    """Under UI_BASE_PATH (e.g. /plan/), route /plan/api/... and /plan/main-x.js as /api/... and /main-x.js.
    Registered last, so it runs first."""
    if config.UI_BASE != "/" and (request.url.path + "/").startswith(config.UI_BASE):
        rest = request.url.path[len(config.UI_BASE) - 1:] or "/"
        request.scope["path"] = rest
        request.scope["raw_path"] = rest.encode()
    return await call_next(request)


@app.get("/api/config")
def runtime_config() -> dict:
    """The UI's runtime config, loaded before it starts: nothing about hosts, ports or paths is compiled into it."""
    return {
        "apiBase": config.UI_BASE + "api/",
        "basePath": config.UI_BASE,
        "publicUrl": config.PUBLIC_URL,
        "frameParents": config.FRAME_ANCESTORS,
        "login": {"enabled": config.LOGIN, "issuer": config.OIDC_ISSUER, "clientId": config.OIDC_CLIENT_ID},
    }


app.include_router(router)


@app.get("/{path:path}", include_in_schema=False)
def ui(path: str):  # type: ignore[no-untyped-def]
    """The built Angular UI: its static files, and index.html (with <base href> set to UI_BASE_PATH) for everything else."""
    if path.startswith("api/") or path == "api":
        raise HTTPException(404)
    root = config.UI_DIR.resolve()
    if path:
        file = (root / path).resolve()
        if file.is_file() and root in file.parents:
            return FileResponse(file)
    index = root / "index.html"
    if not index.is_file():
        raise HTTPException(404, "UI not built")
    page = index.read_text(encoding="utf-8").replace('<base href="/">', f'<base href="{html.escape(config.UI_BASE)}">', 1)
    return HTMLResponse(page, headers={"Cache-Control": "no-store"})
