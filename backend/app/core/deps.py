"""Shared FastAPI dependencies — authentication only for now.

Role/ownership authorization guards are added in Step 3 and will build on
top of `get_current_user` defined here, per CLAUDE.md's "keep authentication
logic centralized" rule.
"""

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import decode_access_token
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)

_credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    token: str | None = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    if token is None:
        raise _credentials_exception

    try:
        payload = decode_access_token(token)
    except jwt.PyJWTError:
        raise _credentials_exception from None

    user_id = payload.get("sub")
    if user_id is None:
        raise _credentials_exception

    user = db.get(User, int(user_id))
    if user is None:
        raise _credentials_exception

    return user
