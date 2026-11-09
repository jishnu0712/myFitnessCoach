"""Assemble the versioned API routers under a single application router."""

from fastapi import APIRouter

from app.api.v1.health import router as health_router

api_router = APIRouter()
api_router.include_router(health_router, prefix="/api/v1")
