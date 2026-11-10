"""Expose authenticated workout creation and owner-scoped history."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.database import get_db_session
from app.models.user import User
from app.schemas.workout import WorkoutCreateRequest, WorkoutResponse
from app.services.workouts import create_workout, get_user_workouts

router = APIRouter(prefix="/workouts", tags=["Workouts"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def post_workout(
    request: WorkoutCreateRequest,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict[str, object]:
    """Save workout data under the authenticated account."""
    workout = await create_workout(session, user.id, request.workout_data)
    return {
        "success": True,
        "data": {"workout": WorkoutResponse.model_validate(workout).model_dump()},
    }


@router.get("")
async def get_workouts(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict[str, object]:
    """Return a page of the authenticated user's workouts only."""
    workouts = await get_user_workouts(session, user.id, limit, offset)
    return {
        "success": True,
        "data": {
            "workouts": [WorkoutResponse.model_validate(item).model_dump() for item in workouts]
        },
    }
