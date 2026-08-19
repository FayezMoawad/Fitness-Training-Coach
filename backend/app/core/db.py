"""Database engine/session setup.

`DATABASE_URL` is required (via env / `.env`) for anything in this module to
be usable; the app can still boot without it (e.g. `/health`), but importing
`SessionLocal`/`get_db` without a configured URL raises a clear error rather
than failing silently.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    pass


engine = create_engine(settings.database_url) if settings.database_url else None
SessionLocal = (
    sessionmaker(autocommit=False, autoflush=False, bind=engine) if engine else None
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a request-scoped DB session."""
    if SessionLocal is None:
        raise RuntimeError(
            "DATABASE_URL is not configured. Set it via the environment or .env file."
        )
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
