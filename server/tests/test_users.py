from __future__ import annotations


def test_create_and_read_user(client) -> None:
    response = client.post("/users/", json={"email": "a@b.com", "password": "secret"})
    assert response.status_code == 200
    user = response.json()
    assert user["id"] == 1
    assert user["email"] == "a@b.com"

    response = client.get(f"/users/{user['id']}")
    assert response.status_code == 200
    user_get = response.json()
    assert user_get["email"] == "a@b.com"
