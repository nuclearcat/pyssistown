from __future__ import annotations


def test_login_and_me(client) -> None:
    client.post("/users/", json={"email": "a@b.com", "password": "secret"})

    response = client.post(
        "/auth/token",
        data={"username": "a@b.com", "password": "secret"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    user = response.json()
    assert user["email"] == "a@b.com"
