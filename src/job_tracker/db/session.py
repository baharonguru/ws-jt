from collections.abc import Generator
from contextlib import contextmanager
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from job_tracker.config import get_settings


@lru_cache
def get_engine() -> Engine:
    """Create one reusable database engine per Python process."""
    settings = get_settings()

    return create_engine(
        settings.database_url,
        pool_pre_ping=True,
    )


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    """Create sessions bound to the application database engine."""
    return sessionmaker(
        bind=get_engine(),
        autoflush=False,
        expire_on_commit=False,
    )


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """
    Provide a transaction-safe database session.

    Successful work commits automatically.
    Any exception rolls the transaction back.
    """
    session = get_session_factory()()

    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()