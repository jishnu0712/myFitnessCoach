"""Owner-scoped database operations for workout records."""

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workout import Workout


async def list_user_workouts(
    session: AsyncSession, user_id: int, limit: int, offset: int
) -> list[Workout]:
    """List only records owned by a user, newest first."""
    result = await session.execute(
        select(Workout)
        .where(Workout.user_id == user_id)
        .order_by(desc(Workout.created_at), desc(Workout.id))
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


def add_workout(session: AsyncSession, workout: Workout) -> None:
    """Add a workout to the current transaction."""
    session.add(workout)
