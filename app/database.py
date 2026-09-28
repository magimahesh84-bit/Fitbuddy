"""
database.py - Database configuration and session management.

Uses SQLAlchemy to connect to a local SQLite database.
The database file (fitbuddy.db) is created automatically on first run.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# SQLite database file path (created in the project root)
DATABASE_URL = "sqlite:///./fitbuddy.db"

# Create the SQLAlchemy engine
# check_same_thread=False is needed for SQLite with FastAPI (multi-threaded)
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Session factory - each request gets its own session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all ORM models
Base = declarative_base()


def get_db():
    """
    Dependency function for FastAPI routes.
    Yields a database session and ensures it is closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
