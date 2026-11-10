"""Persist user accounts and their authorization role."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.workout import Workout


class User(Base):
    """An account that can authenticate and own workout records."""

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('superadmin', 'admin', 'user')", name="valid_role"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, default="user", server_default="user"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    workouts: Mapped[list["Workout"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
