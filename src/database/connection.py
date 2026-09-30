"""Database Engine, Session Management, and Schema Initializer."""

import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.database.models import Base
from src.utils.config import settings
from src.utils.logger import get_logger

logger = get_logger("database")

# Handle SQLite vs PostgreSQL arguments
connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    echo=False,
    pool_pre_ping=True if not settings.database_url.startswith("sqlite") else False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Create all tables in the database if they do not exist."""
    logger.info(f"Initializing database schema at {settings.database_url}")
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema initialized successfully.")


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Context manager for safe transactional database sessions."""
    session: Session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session rolled back due to error: {e}")
        raise
    finally:
        session.close()
