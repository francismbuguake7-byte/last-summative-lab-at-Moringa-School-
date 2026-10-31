from tests.helpers import register


def test_create_and_update_validate_event_data(client):
    register(client)
    assert client.post("/events", json={}).status_code == 400
    assert client.post("/events", json={"title": " "}).status_code == 400
    assert client.post(
        "/events", json={"title": "Plan", "user_id": 99}
    ).status_code == 400
    created = client.post("/events", json={"title": "Plan"})
    event_id = created.json["id"]
    updated = client.patch(
        f"/events/{event_id}", json={"description": "Set priorities"}
    )
    assert updated.status_code == 200
    assert updated.json["title"] == "Plan"
    assert updated.json["description"] == "Set priorities"
    assert client.patch(f"/events/{event_id}", json={}).status_code == 400


def test_get_owned_event(client):
    register(client)
    created = client.post(
        "/events", json={"title": "Plan the week", "description": "Set priorities"}
    )
    event_id = created.json["id"]
    response = client.get(f"/events/{event_id}")
    assert response.status_code == 200
    assert response.json["id"] == event_id
    assert response.json["title"] == "Plan the week"
    assert response.json["description"] == "Set priorities"
    assert client.get("/events/999").status_code == 404


def test_delete_owned_event(client):
    register(client)
    event = client.post("/events", json={"title": "Temporary"}).json
    assert client.delete(f"/events/{event['id']}").status_code == 204
    assert client.get("/events").json["pagination"]["total"] == 0
    assert client.delete(f"/events/{event['id']}").status_code == 404
