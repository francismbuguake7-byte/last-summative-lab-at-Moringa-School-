from app import app
from models import Event, db
from tests.helpers import register


def test_users_cannot_access_each_others_events(client):
    register(client)
    event = client.post("/events", json={"title": "Private event"}).json
    client.post("/logout")
    register(client, username="bob")
    assert client.get("/events").json["events"] == []
    assert client.get(f"/events/{event['id']}").status_code == 404
    assert client.patch(
        f"/events/{event['id']}", json={"title": "Stolen"}
    ).status_code == 404
    assert client.delete(f"/events/{event['id']}").status_code == 404
    with app.app_context():
        stored = db.session.get(Event, event["id"])
        assert stored.title == "Private event"
