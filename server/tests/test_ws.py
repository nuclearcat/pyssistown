from __future__ import annotations

import pytest
from starlette.websockets import WebSocketDisconnect


def test_ws_requires_token(client) -> None:
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect("/ws/game?room=main"):
            pass
    assert exc.value.code == 1008


def test_ws_echo(client) -> None:
    client.post("/users/", json={"email": "a@b.com", "password": "secret"})
    token_resp = client.post(
        "/auth/token",
        data={"username": "a@b.com", "password": "secret"},
    )
    token = token_resp.json()["access_token"]

    with client.websocket_connect(f"/ws/game?room=main&token={token}") as ws:
        ws.send_text("ping")
        data = ws.receive_text()
        assert data == "ping"
