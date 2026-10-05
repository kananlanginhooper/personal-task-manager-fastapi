from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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
    """Optional shared-token check until a real sign-in sits in front of the API."""
    if config.API_TOKEN and request.url.path.startswith("/api") and request.method != "OPTIONS":
        if request.headers.get("authorization") != f"Bearer {config.API_TOKEN}":
            return JSONResponse({"detail": "Sign-in required"}, status_code=401)
    return await call_next(request)


app.include_router(router)
