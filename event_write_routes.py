from flask import Blueprint, g, jsonify

from api_helpers import json_object, login_required
from event_helpers import event_payload, validate_event_fields
from models import Event, db


event_writes = Blueprint("event_writes", __name__)


@event_writes.post("/events")
@login_required
def create_event():
    data, error = validate_event_fields(json_object(), creating=True)
    if error:
        return jsonify({"error": error}), 400
    event = Event(
        title=data["title"].strip(),
        description=data.get("description", "").strip(),
        user_id=g.current_user.id,
    )
    db.session.add(event)
    db.session.commit()
    return jsonify(event_payload(event)), 201


@event_writes.patch("/events/<int:event_id>")
@login_required
def update_event(event_id):
    data, error = validate_event_fields(json_object())
    if error:
        return jsonify({"error": error}), 400
    event = Event.query.filter_by(id=event_id, user_id=g.current_user.id).first()
    if event is None:
        return jsonify({"error": "Event not found"}), 404
    for field in ("title", "description"):
        if field in data:
            setattr(event, field, data[field].strip())
    db.session.commit()
    return jsonify(event_payload(event)), 200


@event_writes.delete("/events/<int:event_id>")
@login_required
def delete_event(event_id):
    event = Event.query.filter_by(id=event_id, user_id=g.current_user.id).first()
    if event is None:
        return jsonify({"error": "Event not found"}), 404
    db.session.delete(event)
    db.session.commit()
    return "", 204
