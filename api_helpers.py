from functools import wraps

from flask import g, jsonify, request, session

from models import User, db


def json_object():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else None


def user_payload(user):
    return {"id": user.id, "username": user.username}


def password_byte_length(password):
    try:
        return len(password.encode("utf-8"))
    except UnicodeEncodeError:
        return None


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        user_id = session.get("user_id")
        user = db.session.get(User, user_id) if user_id else None
        if user is None:
            session.clear()
            return jsonify({"error": "Authentication required"}), 401
        g.current_user = user
        return view(*args, **kwargs)

    return wrapped_view
