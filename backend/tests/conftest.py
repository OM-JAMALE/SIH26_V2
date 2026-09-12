import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Force test database configuration before importing app models/session
settings.database_url = "sqlite:///./test_health_ai.db"
settings.ai_provider = "mock"

from app.main import app as fastapi_app
import app.db.session as db_session_module
from app.db.session import Base, get_db
import app.db.models  # Register all ORM models into Base.metadata

engine = create_engine(
    settings.database_url, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Ensure application database session uses the test engine
db_session_module.engine = engine
db_session_module.SessionLocal = TestingSessionLocal


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Cleanly delete rows from all tables rather than dropping schema
        with engine.connect() as conn:
            for table in reversed(Base.metadata.sorted_tables):
                try:
                    conn.execute(table.delete())
                except Exception:
                    pass
            conn.commit()


@pytest.fixture(scope="function")
def client(db_session):
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    fastapi_app.dependency_overrides[get_db] = _override_get_db
    with TestClient(fastapi_app, raise_server_exceptions=False) as c:
        yield c
    fastapi_app.dependency_overrides.clear()
