from models import User

from app import app
from tests.helpers import register


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
    assert client.post("/signup", json={"username": "al", "password": "Password123!"}).status_code == 400
    assert client.post("/signup", json={"username": "alice", "password": "short"}).status_code == 400
    assert register(client).status_code == 201
    assert register(client, username="ALICE").status_code == 409
