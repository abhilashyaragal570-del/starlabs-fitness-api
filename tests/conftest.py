import os

# Must be set before the app is imported so tests use their own database file.
os.environ["DATABASE_URL"] = "sqlite:///./test_fitness.db"
os.environ.setdefault("SECRET_KEY", "test-secret-key-only-for-tests-0123456789abcdef")

import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c