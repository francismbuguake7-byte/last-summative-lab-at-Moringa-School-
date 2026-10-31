from tests.helpers import register


def test_protected_event_routes_require_authentication(client):
    assert client.get("/events").status_code == 401
    assert client.post("/events", json={"title": "Plan"}).status_code == 401
    assert client.get("/events/1").status_code == 401
    assert client.patch("/events/1", json={"title": "Updated"}).status_code == 401
    assert client.delete("/events/1").status_code == 401


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
        "page": 1, "per_page": 1, "total": 2, "pages": 2
    }
    assert client.get("/events?page=0").status_code == 400
    assert client.get("/events?per_page=101").status_code == 400
    assert client.get("/events?page=invalid").status_code == 400
