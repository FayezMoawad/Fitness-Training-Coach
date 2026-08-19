"""Shared FastAPI dependencies: authentication and role-based authorization.

`require_role` handles the "is this the right kind of user at all" check
(coach-only vs client-only routes). Ownership checks — "is this *specific*
resource this user's" — are a separate concern and live in
`app.services.authorization`, since they need the resource loaded first;
see that module for the 403-vs-404 convention used there.
"""

from collections.abc import Callable

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import decode_access_token
from app.models.user import User, UserRole

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


def require_role(role: UserRole) -> Callable[[User], User]:
    """Dependency factory restricting a route to a single role.

    Usage: `current_user: User = Depends(require_role(UserRole.coach))`.
    A mismatched role returns 403 — unlike an ownership violation, there's
    no information to leak here: the caller already knows their own role.
    """

    def _require_role(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return current_user

    return _require_role
