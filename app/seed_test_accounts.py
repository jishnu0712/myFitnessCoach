"""Explicitly seed repeat-safe test accounts in development or test environments."""

import asyncio
import os

from dotenv import dotenv_values
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import SessionFactory
from app.core.security import hash_password
from app.models.user import User
from app.repositories.users import get_user_by_email

ROLE_ENV_NAMES = {
    "superadmin": "SUPERADMIN",
    "admin": "ADMIN",
    "user": "USER",
}


def load_seed_accounts() -> list[tuple[str, str, str]]:
    """Read and validate one email/password pair for each role from the environment."""
    file_values = dotenv_values(".env")

    def get_value(name: str) -> str:
        """Read a setting from the process environment or the local env file."""
        return os.getenv(name, file_values.get(name) or "")

    accounts: list[tuple[str, str, str]] = []
    seen_emails: set[str] = set()
    for role, suffix in ROLE_ENV_NAMES.items():
        email = get_value(f"SEED_{suffix}_EMAIL").strip().lower()
        password = get_value(f"SEED_{suffix}_PASSWORD")
        if not email or not password:
            raise ValueError(f"SEED_{suffix}_EMAIL and SEED_{suffix}_PASSWORD are required")
        if len(password) < 8:
            raise ValueError(f"SEED_{suffix}_PASSWORD must be at least 8 characters")
        if email in seen_emails:
            raise ValueError("Seed account emails must be unique")
        seen_emails.add(email)
        accounts.append((role, email, password))
    return accounts


async def seed_test_accounts(session: AsyncSession) -> int:
    """Create missing configured accounts without changing existing accounts."""
    settings = get_settings()
    if settings.app_env not in {"development", "test"}:
        raise RuntimeError("Test accounts may only be seeded in development or test environments")

    created = 0
    for role, email, password in load_seed_accounts():
        if await get_user_by_email(session, email) is not None:
            continue
        session.add(User(email=email, password_hash=hash_password(password), role=role))
        created += 1
    await session.commit()
    return created


async def main() -> None:
    """Run the seeder as an explicit command, never as application startup work."""
    async with SessionFactory() as session:
        created = await seed_test_accounts(session)
    print(f"Seed complete; created {created} account(s).")


if __name__ == "__main__":
    asyncio.run(main())
