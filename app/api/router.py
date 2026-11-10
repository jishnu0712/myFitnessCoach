"""Assemble the versioned API routers under a single application router."""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.health import router as health_router
from app.api.v1.workouts import router as workouts_router

api_router = APIRouter()
api_router.include_router(health_router, prefix="/api/v1")
api_router.include_router(auth_router, prefix="/api/v1")
api_router.include_router(workouts_router, prefix="/api/v1")
