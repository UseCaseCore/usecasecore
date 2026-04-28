from __future__ import annotations

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    """Base class for the example SQLAlchemy models."""


def create_engine_for_url(database_url: str = "sqlite+pysqlite:///:memory:") -> Engine:
    """Create an engine suitable for the demo and tests.

    SQLite keeps the example runnable without Docker. The naming and table
    boundaries are intentionally close to what a Postgres-backed app would use.
    """

    if database_url in {"sqlite:///:memory:", "sqlite+pysqlite:///:memory:"}:
        return create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            future=True,
        )

    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, connect_args=connect_args, future=True)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def create_schema(engine: Engine) -> None:
    # Import models so SQLAlchemy registers them on Base.metadata.
    from . import models  # noqa: F401

    Base.metadata.create_all(engine)
