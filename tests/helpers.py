def register(client, username="alice"):
    return client.post(
        "/signup", json={"username": username, "password": "Password123!"}
    )
