from __future__ import annotations

import html
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

from app.api.routes import api_router
from app.core.config import settings
from app.db.session import create_all
from app.services.common import InvalidRequestError, NotFoundError


@asynccontextmanager
async def lifespan(_: FastAPI):  # type: ignore[no-untyped-def]
    create_all()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Personal Task Manager API", version="0.2.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # Starlette runs the last-registered middleware first: strip_base_path, then frame_policy, then require_token.
    app.middleware("http")(require_token)
    app.middleware("http")(frame_policy)
    app.middleware("http")(strip_base_path)
    app.add_exception_handler(NotFoundError, lambda _, e: JSONResponse({"detail": str(e)}, status_code=404))
    app.add_exception_handler(InvalidRequestError, lambda _, e: JSONResponse({"detail": str(e)}, status_code=400))
    app.include_router(api_router)
    app.get("/{path:path}", include_in_schema=False)(ui)
    return app


async def require_token(request: Request, call_next):  # type: ignore[no-untyped-def]
    """Optional shared-token check until a real sign-in sits in front of the API.
    /api/config stays open: the UI needs it first."""
    path = request.url.path
    if settings.api_token and path.startswith("/api") and path != "/api/config" and request.method != "OPTIONS":
        if request.headers.get("authorization") != f"Bearer {settings.api_token}":
            return JSONResponse({"detail": "Sign-in required"}, status_code=401)
    return await call_next(request)


async def frame_policy(request: Request, call_next):  # type: ignore[no-untyped-def]
    """Only this app and the configured wrapper origins may show it in an iframe."""
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = "frame-ancestors " + " ".join(["'self'", *settings.frame_ancestor_list])
    return response


async def strip_base_path(request: Request, call_next):  # type: ignore[no-untyped-def]
    """Under UI_BASE_PATH (e.g. /plan/), route /plan/api/... and /plan/main-x.js as /api/... and /main-x.js."""
    base = settings.ui_base
    if base != "/" and (request.url.path + "/").startswith(base):
        rest = request.url.path[len(base) - 1 :] or "/"
        request.scope["path"] = rest
        request.scope["raw_path"] = rest.encode()
    return await call_next(request)


def ui(path: str):  # type: ignore[no-untyped-def]
    """The built Angular UI: its static files, and index.html (with <base href> set to UI_BASE_PATH) for everything else."""
    if path.startswith("api/") or path == "api":
        raise HTTPException(404)
    root = settings.ui_dir.resolve()
    if path:
        file = (root / path).resolve()
        if file.is_file() and root in file.parents:
            return FileResponse(file)
    index = root / "index.html"
    if not index.is_file():
        raise HTTPException(404, "UI not built")
    page = index.read_text(encoding="utf-8").replace('<base href="/">', f'<base href="{html.escape(settings.ui_base)}">', 1)
    return HTMLResponse(page, headers={"Cache-Control": "no-store"})


app = create_app()
