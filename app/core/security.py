"""Password hashing and signed access-token helpers."""

from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from app.core.config import get_settings

password_hasher = PasswordHash.recommended()
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    """Return an Argon2id password hash; never persist the raw password."""
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a submitted password against its stored Argon2id hash."""
    try:
        return password_hasher.verify(password, password_hash)
    except (ValueError, TypeError):
        return False


def create_access_token(user_id: int) -> str:
    """Sign a short-lived access token for a persisted account."""
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.auth_secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> int | None:
    """Validate a signed, unexpired access token and return its user ID."""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.auth_secret_key,
            algorithms=[ALGORITHM],
            options={"require": ["sub", "exp", "type"]},
        )
        subject = payload.get("sub")
        if payload.get("type") != "access" or not isinstance(subject, str):
            return None
        user_id = int(subject)
        return user_id if user_id > 0 else None
    except (jwt.PyJWTError, TypeError, ValueError):
        return None
