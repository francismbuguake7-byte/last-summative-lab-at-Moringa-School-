from tests.helpers import register


def test_login_logout_and_session_check(client):
    register(client)
    client.post("/logout")
    response = client.post(
        "/login", json={"username": "ALICE", "password": "Password123!"}
    )
    assert response.status_code == 200
    assert response.json == {"id": 1, "username": "alice"}
    assert client.get("/me").status_code == 200
    assert client.post("/logout").status_code == 204
    assert client.get("/check_session").status_code == 401
    assert client.post(
        "/login", json={"username": "alice", "password": "incorrect"}
    ).status_code == 401
    assert client.post(
        "/login", json={"username": "alice", "password": "x" * 73}
    ).status_code == 400


def test_frontend_origin_can_send_session_credentials(client):
    response = client.get(
        "/check_session", headers={"Origin": "http://localhost:3000"}
    )
    assert response.headers["Access-Control-Allow-Origin"] == "http://localhost:3000"
    assert response.headers["Access-Control-Allow-Credentials"] == "true"
    untrusted = client.get(
        "/check_session", headers={"Origin": "https://untrusted.example"}
    )
    assert "Access-Control-Allow-Origin" not in untrusted.headers
