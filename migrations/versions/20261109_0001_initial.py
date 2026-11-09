"""Create the initial migration baseline before domain tables are introduced."""

from collections.abc import Sequence

revision: str = "20261109_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Apply the empty baseline; the application has no domain tables yet."""


def downgrade() -> None:
    """Revert the empty baseline without changing application data."""
