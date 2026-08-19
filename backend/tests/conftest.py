"""Shared pytest fixtures for model/DB tests.

Requires a reachable PostgreSQL instance, configured via `TEST_DATABASE_URL`
(falls back to `DATABASE_URL` if unset). The schema is created once per test
session from the SQLAlchemy models (`Base.metadata`) — not via Alembic —
and dropped again at the end; each test runs inside its own transaction
that is rolled back afterwards, so tests never see each other's data.
"""

import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.models import Base

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL")


@pytest.fixture(scope="session")
def engine():
    if not TEST_DATABASE_URL:
        pytest.skip(
            "TEST_DATABASE_URL (or DATABASE_URL) is not set; "
            "point it at a PostgreSQL test database to run DB tests."
        )
    eng = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture
def db_session(engine) -> Session:
    connection = engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()
        # A failed flush (e.g. an expected IntegrityError/DataError in a
        # test) already deactivates the transaction; only roll back if it's
        # still active to avoid a harmless-but-noisy SAWarning.
        if transaction.is_active:
            transaction.rollback()
        connection.close()
