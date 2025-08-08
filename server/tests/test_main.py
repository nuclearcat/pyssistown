from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[2]))

from server.app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_root() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
