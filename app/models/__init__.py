"""Import all SQLAlchemy models so Alembic can discover their metadata."""

from app.models.user import User
from app.models.workout import Workout

__all__ = ["User", "Workout"]
