from __future__ import annotations

from sqlmodel import SQLModel, create_engine, Session

DATABASE_URL = "sqlite:///./pyssistown.db"

engine = create_engine(
    DATABASE_URL, echo=False, connect_args={"check_same_thread": False}
)


def init_db() -> None:
    """Create database tables."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    """Provide a transactional scope around a series of operations."""
    with Session(engine) as session:
        yield session
