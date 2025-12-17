"""
Database configuration and session management
"""
from sqlmodel import SQLModel, create_engine, Session
from contextlib import contextmanager
import os

# Get absolute path to database.db in project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database.db")
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DB_PATH}")

# Fix for Render/Heroku Postgres URL (postgres:// -> postgresql://)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create engine
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)

def create_db_and_tables():
    """Create all database tables"""
    SQLModel.metadata.create_all(engine)

@contextmanager
def get_session():
    """Get database session"""
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

# Dependency for FastAPI
def get_db_session():
    """FastAPI dependency for database session"""
    with get_session() as session:
        yield session
