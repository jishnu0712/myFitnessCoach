"""Persist flexible workout data owned by a user."""

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, DateTime, ForeignKey, Index, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class Workout(Base):
    """A single user-owned workout record with structured JSON data."""

    __tablename__ = "workouts"
    __table_args__ = (Index("ix_workouts_user_id_created_at", "user_id", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    workout_data: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    user: Mapped["User"] = relationship(back_populates="workouts")
