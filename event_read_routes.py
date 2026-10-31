from flask import Blueprint, g, jsonify, request

from api_helpers import login_required
from event_helpers import event_payload
from models import Event


event_reads = Blueprint("event_reads", __name__)


@event_reads.get("/events")
@login_required
def list_events():
    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 10))
    except ValueError:
        return jsonify({"error": "page and per_page must be integers"}), 400
    if page < 1 or not 1 <= per_page <= 100:
        return jsonify({"error": "page must be positive and per_page must be 1-100"}), 400

    result = (
        Event.query.filter_by(user_id=g.current_user.id)
        .order_by(Event.id)
        .paginate(page=page, per_page=per_page, error_out=False)
    )
    return jsonify(
        {
            "events": [event_payload(event) for event in result.items],
            "pagination": {
                "page": result.page,
                "per_page": result.per_page,
                "total": result.total,
                "pages": result.pages,
            },
        }
    ), 200


@event_reads.get("/events/<int:event_id>")
@login_required
def get_event(event_id):
    event = Event.query.filter_by(id=event_id, user_id=g.current_user.id).first()
    if event is None:
        return jsonify({"error": "Event not found"}), 404
    return jsonify(event_payload(event)), 200
