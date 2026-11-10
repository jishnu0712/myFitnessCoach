"""Persist and retrieve workouts while enforcing user ownership."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workout import Workout
from app.repositories.workouts import add_workout, list_user_workouts


async def create_workout(
    session: AsyncSession, user_id: int, workout_data: dict[str, object]
) -> Workout:
    """Create a workout record owned by the authenticated user."""
    workout = Workout(user_id=user_id, workout_data=workout_data)
    add_workout(session, workout)
    await session.commit()
    await session.refresh(workout)
    return workout


async def get_user_workouts(
    session: AsyncSession, user_id: int, limit: int, offset: int
) -> list[Workout]:
    """Return a page of records belonging exclusively to the authenticated user."""
    return await list_user_workouts(session, user_id, limit, offset)
