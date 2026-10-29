from fastapi import APIRouter

from app.api.routes import log, planner, system, tasks

api_router = APIRouter(prefix="/api")
for module in (system, tasks, planner, log):
    api_router.include_router(module.router)
