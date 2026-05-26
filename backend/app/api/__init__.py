from fastapi import APIRouter

from app.api.agents import router as agents_router
from app.api.channels import router as channels_router
from app.api.executions import router as executions_router
from app.api.templates import router as templates_router
from app.api.workflows import router as workflows_router
from app.api.ws import router as ws_router

api_router = APIRouter()
api_router.include_router(agents_router, prefix="/agents", tags=["agents"])
api_router.include_router(workflows_router, prefix="/workflows", tags=["workflows"])
api_router.include_router(executions_router, prefix="/executions", tags=["executions"])
api_router.include_router(channels_router, prefix="/channels", tags=["channels"])
api_router.include_router(templates_router, prefix="/templates", tags=["templates"])
api_router.include_router(ws_router, tags=["websocket"])

__all__ = ["api_router"]
