"""Centralized password hashing and JWT helpers.

All auth logic goes through this module — nothing outside it should call
`jwt.encode`/`jwt.decode` or a hashing library directly, per CLAUDE.md's
"keep authentication logic centralized" rule.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from passlib.context import CryptContext

from app.core.config import settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

_JWT_ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return _pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    *, subject: str, role: str, expires_delta: timedelta | None = None
) -> str:
    if not settings.jwt_secret:
        raise RuntimeError(
            "JWT_SECRET is not configured. Set it via the environment or .env file."
        )

    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.jwt_expire_minutes)
    )
    payload: dict[str, Any] = {"sub": subject, "role": role, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=_JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT. Raises `jwt.PyJWTError` (or a subclass,
    e.g. `jwt.ExpiredSignatureError`) if the token is missing, malformed,
    expired, or has an invalid signature — callers are expected to catch
    `jwt.PyJWTError` and translate it into a 401 response."""
    if not settings.jwt_secret:
        raise RuntimeError(
            "JWT_SECRET is not configured. Set it via the environment or .env file."
        )
    return jwt.decode(token, settings.jwt_secret, algorithms=[_JWT_ALGORITHM])
