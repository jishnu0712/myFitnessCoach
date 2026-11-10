"""Small in-memory AsyncSession substitute for API contract tests."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.sql import visitors
from sqlalchemy.sql.elements import BinaryExpression, BindParameter

from app.models.user import User
from app.models.workout import Workout


class FakeResult:
    """Expose the subset of SQLAlchemy result methods used by repositories."""

    def __init__(self, rows: list[Any]) -> None:
        self.rows = rows

    def scalar_one_or_none(self) -> Any | None:
        return self.rows[0] if self.rows else None

    def scalars(self) -> "FakeResult":
        return self

    def all(self) -> list[Any]:
        return self.rows


class FakeSession:
    """Persist users and workouts in memory while honoring repository filters."""

    def __init__(self) -> None:
        self.users: list[User] = []
        self.workouts: list[Workout] = []
        self.pending: list[User | Workout] = []
        self.next_user_id = 1
        self.next_workout_id = 1

    async def execute(self, statement: Any) -> FakeResult:
        entity = statement.column_descriptions[0]["entity"]
        filters: dict[str, Any] = {}
        if statement.whereclause is not None:
            for expression in visitors.iterate(statement.whereclause):
                if (
                    isinstance(expression, BinaryExpression)
                    and hasattr(expression.left, "key")
                    and isinstance(expression.right, BindParameter)
                ):
                    filters[expression.left.key] = expression.right.value

        if entity is User:
            rows = [
                user
                for user in self.users
                if all(getattr(user, key) == value for key, value in filters.items())
            ]
            return FakeResult(rows[:1])

        if entity is Workout:
            rows = [
                workout
                for workout in self.workouts
                if all(getattr(workout, key) == value for key, value in filters.items())
            ]
            rows.sort(key=lambda item: (item.created_at, item.id), reverse=True)
            parameters = statement.compile().params
            offset = next(
                (value for key, value in parameters.items() if "param_" in key and value == 0), 0
            )
            limit = next((value for key, value in parameters.items() if value == 50), len(rows))
            return FakeResult(rows[offset : offset + limit])

        raise AssertionError(f"Unsupported query entity: {entity}")

    def add(self, instance: User | Workout) -> None:
        self.pending.append(instance)

    async def commit(self) -> None:
        for instance in self.pending:
            instance.created_at = datetime.now(UTC)
            if isinstance(instance, User):
                instance.id = self.next_user_id
                self.next_user_id += 1
                self.users.append(instance)
            else:
                instance.id = self.next_workout_id
                self.next_workout_id += 1
                self.workouts.append(instance)
        self.pending.clear()

    async def refresh(self, instance: User | Workout) -> None:
        del instance

    async def rollback(self) -> None:
        self.pending.clear()
