def event_payload(event):
    return {
        "id": event.id,
        "title": event.title,
        "description": event.description,
        "created_at": event.created_at.isoformat(),
    }


def validate_event_fields(data, creating=False):
    if data is None:
        return None, "A JSON object is required"
    allowed_fields = {"title", "description"}
    if not data or not data.keys() <= allowed_fields:
        return None, "Provide title and/or description fields only"
    if creating and "title" not in data:
        return None, "The title field is required"

    for field in ("title", "description"):
        if field in data and not isinstance(data[field], str):
            return None, f"{field.capitalize()} must be a string"
    if "title" in data and not data["title"].strip():
        return None, "Title cannot be empty"
    return data, None
