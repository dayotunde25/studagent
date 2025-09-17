"""
Database configuration and session management.
"""
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.orm import sessionmaker
from app.core.config import settings


# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
)


def create_db_and_tables():
    """Create database tables."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    """Get database session."""
    with Session(engine) as session:
        yield session


# Session maker for synchronous operations
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)