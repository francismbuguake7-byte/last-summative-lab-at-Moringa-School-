import pytest
from sqlalchemy import create_engine

from app import app
from models import Event, User, db


@pytest.fixture(autouse=True)
def reset_database():
    app.config.update(
        TESTING=True,
        SECRET_KEY="test-secret",
    )
    with app.app_context():
        original_engine = db.engines[None]
        test_engine = create_engine("sqlite:///:memory:")
        db.engines[None] = test_engine
    try:
        with app.app_context():
            db.session.remove()
            db.drop_all()
            db.create_all()
        yield
    finally:
        with app.app_context():
            db.session.remove()
            db.drop_all()
            db.engines[None] = original_engine
        test_engine.dispose()


@pytest.fixture
def client():
    return app.test_client()


def register(client, username="alice"):
    return client.post(
        "/signup", json={"username": username, "password": "Password123!"}
    )


def test_signup_hashes_password_and_check_session(client):
    response = register(client)
    assert response.status_code == 201
    assert response.json == {"id": 1, "username": "alice"}

    with app.app_context():
        user = User.query.filter_by(username="alice").one()
        assert user.password_hash != "Password123!"
        assert user.check_password("Password123!")

    assert client.get("/check_session").json == response.json


def test_signup_validates_input_and_unique_usernames(client):
    assert (
        client.post(
            "/signup", json={"username": "al", "password": "Password123!"}
        ).status_code
        == 400
    )
    assert (
        client.post(
            "/signup", json={"username": "alice", "password": "short"}
        ).status_code
        == 400
    )
    assert register(client).status_code == 201
    duplicate = register(client, username="ALICE")
    assert duplicate.status_code == 409


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


def test_protected_event_routes_require_authentication(client):
    assert client.get("/events").status_code == 401
    assert client.post("/events", json={"title": "Plan"}).status_code == 401
    assert client.patch("/events/1", json={"title": "Updated"}).status_code == 401
    assert client.delete("/events/1").status_code == 401


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


def test_create_list_and_paginate_events(client):
    register(client)
    created = client.post(
        "/events", json={"title": "Plan the week", "description": "Set priorities"}
    )
    assert created.status_code == 201
    assert created.json["title"] == "Plan the week"
    assert created.json["description"] == "Set priorities"

    client.post("/events", json={"title": "Review progress"})
    response = client.get("/events?page=1&per_page=1")
    assert response.status_code == 200
    assert len(response.json["events"]) == 1
    assert response.json["pagination"] == {
        "page": 1,
        "per_page": 1,
        "total": 2,
        "pages": 2,
    }

    assert client.get("/events?page=0").status_code == 400
    assert client.get("/events?per_page=101").status_code == 400
    assert client.get("/events?page=invalid").status_code == 400


def test_create_and_update_validate_event_data(client):
    register(client)
    assert client.post("/events", json={}).status_code == 400
    assert client.post("/events", json={"title": " "}).status_code == 400
    assert (
        client.post(
            "/events", json={"title": "Plan", "user_id": 99}
        ).status_code
        == 400
    )

    created = client.post("/events", json={"title": "Plan"})
    event_id = created.json["id"]
    updated = client.patch(
        f"/events/{event_id}", json={"description": "Set priorities"}
    )
    assert updated.status_code == 200
    assert updated.json["title"] == "Plan"
    assert updated.json["description"] == "Set priorities"
    assert client.patch(f"/events/{event_id}", json={}).status_code == 400


def test_users_cannot_read_update_or_delete_each_others_events(client):
    register(client)
    event = client.post("/events", json={"title": "Private event"}).json

    client.post("/logout")
    register(client, username="bob")
    assert client.get("/events").json["events"] == []
    assert client.patch(
        f"/events/{event['id']}", json={"title": "Stolen"}
    ).status_code == 404
    assert client.delete(f"/events/{event['id']}").status_code == 404

    with app.app_context():
        stored = db.session.get(Event, event["id"])
        assert stored.title == "Private event"


def test_delete_owned_event(client):
    register(client)
    event = client.post("/events", json={"title": "Temporary"}).json
    assert client.delete(f"/events/{event['id']}").status_code == 204
    assert client.get("/events").json["pagination"]["total"] == 0
    assert client.delete(f"/events/{event['id']}").status_code == 404
