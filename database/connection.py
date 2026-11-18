"""SQLAlchemy connection management and session lifecycle with SQLite WAL support."""

from contextlib import contextmanager
import logging
import os
from pathlib import Path
from typing import Any, Generator
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from config import get_settings

logger = logging.getLogger("opensource_radar.database")

Base = declarative_base()

_engine: Engine | None = None
_SessionFactory: sessionmaker | None = None


def get_engine() -> Engine:
    """Create or return the singleton SQLAlchemy engine."""
    global _engine
    if _engine is None:
        settings = get_settings()
        db_url = settings.DATABASE_URL

        # Ensure sqlite parent directory exists
        if db_url.startswith("sqlite:///"):
            raw_path = db_url.replace("sqlite:///", "")
            Path(raw_path).parent.mkdir(parents=True, exist_ok=True)

        connect_args = {}
        if db_url.startswith("sqlite"):
            connect_args = {"check_same_thread": False, "timeout": 30}

        _engine = create_engine(
            db_url,
            connect_args=connect_args,
            pool_pre_ping=True,
            echo=False,
        )

        # Enforce WAL mode and foreign keys on SQLite connections
        if db_url.startswith("sqlite"):
            @event.listens_for(_engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                try:
                    cursor.execute("PRAGMA journal_mode=WAL;")
                    cursor.execute("PRAGMA synchronous=NORMAL;")
                    cursor.execute("PRAGMA foreign_keys=ON;")
                except Exception as exc:
                    logger.warning(f"Failed setting SQLite PRAGMA: {exc}")
                finally:
                    cursor.close()

    return _engine


def get_session_factory() -> sessionmaker:
    """Return the configured sessionmaker."""
    global _SessionFactory
    if _SessionFactory is None:
        engine = get_engine()
        _SessionFactory = sessionmaker(
            bind=engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
    return _SessionFactory


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Safe context manager for database session lifecycle."""
    session_factory = get_session_factory()
    session: Session = session_factory()
    try:
        yield session
        session.commit()
    except Exception as exc:
        session.rollback()
        logger.error(f"Database session rolled back due to error: {exc}")
        raise
    finally:
        session.close()


def init_db() -> None:
    """Initialize database tables safely without recreating existing tables blindly."""
    engine = get_engine()
    # Import models here to register metadata
    from database import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema initialized successfully.")


def check_db_health() -> dict[str, Any]:
    """Check database connection and return status and table counts."""
    from typing import Any
    try:
        with get_db() as session:
            session.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "url": get_settings().DATABASE_URL,
            "connected": True,
        }
    except Exception as exc:
        logger.error(f"Database health check failed: {exc}")
        return {
            "status": "unhealthy",
            "url": get_settings().DATABASE_URL,
            "connected": False,
            "error": str(exc),
        }
