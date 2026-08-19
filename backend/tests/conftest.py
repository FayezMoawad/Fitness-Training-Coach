"""Shared pytest fixtures for model/DB tests.

Requires a reachable PostgreSQL instance, configured via `TEST_DATABASE_URL`
(falls back to `DATABASE_URL` if unset). The schema is created once per test
session from the SQLAlchemy models (`Base.metadata`) — not via Alembic —
and dropped again at the end; each test runs inside its own transaction
that is rolled back afterwards, so tests never see each other's data.
"""

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.core.db import get_db
from app.main import app
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

    # Application code (e.g. auth_service) calls `session.commit()`. A plain
    # commit on a session bound to this connection would commit the outer
    # `transaction` too, leaking data across tests. Nest everything inside a
    # SAVEPOINT and restart it after each commit, per SQLAlchemy's documented
    # pattern for joining a session into an external transaction, so
    # `session.commit()` only ends the savepoint — the outer transaction
    # (and therefore full test isolation) is preserved until teardown.
    session.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def _restart_savepoint(sess, trans):
        if trans.nested and not trans._parent.nested:
            sess.begin_nested()

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


@pytest.fixture
def client(db_session) -> TestClient:
    """A TestClient wired so every request in the test uses `db_session`
    (and therefore rolls back with it), plus a sanity check that JWT_SECRET
    is actually configured — auth routes need it to issue/verify tokens."""
    if not settings.jwt_secret:
        pytest.skip(
            "JWT_SECRET is not set; export it (any non-empty value works for "
            "tests) to run auth tests."
        )

    def _get_db_override():
        yield db_session

    app.dependency_overrides[get_db] = _get_db_override
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
