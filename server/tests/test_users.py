from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[2]))

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.pool import StaticPool

from server.app.main import app
from server.app.db import get_session


def get_test_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    def get_session_override():
        with Session(engine) as session:
            yield session

    return get_session_override


def test_create_and_read_user() -> None:
    override = get_test_session()
    app.dependency_overrides[get_session] = override
    client = TestClient(app)

    response = client.post("/users/", json={"email": "a@b.com", "password": "secret"})
    assert response.status_code == 200
    user = response.json()
    assert user["id"] == 1
    assert user["email"] == "a@b.com"

    response = client.get(f"/users/{user['id']}")
    assert response.status_code == 200
    user_get = response.json()
    assert user_get["email"] == "a@b.com"

    app.dependency_overrides.clear()
