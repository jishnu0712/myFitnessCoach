"""Create user accounts and user-owned workout records."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261110_0002"
down_revision: str | None = "20261109_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create users and workouts with role validation and ownership constraints."""
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), server_default="user", nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("role IN ('superadmin', 'admin', 'user')", name="valid_role"),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "workouts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("workout_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_workouts_user_id_users", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_workouts"),
    )
    op.create_index("ix_workouts_user_id", "workouts", ["user_id"], unique=False)
    op.create_index(
        "ix_workouts_user_id_created_at", "workouts", ["user_id", "created_at"], unique=False
    )


def downgrade() -> None:
    """Drop workouts before their owning user records."""
    op.drop_index("ix_workouts_user_id_created_at", table_name="workouts")
    op.drop_index("ix_workouts_user_id", table_name="workouts")
    op.drop_table("workouts")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
