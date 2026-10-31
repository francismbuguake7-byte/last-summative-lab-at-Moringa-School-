from flask import Blueprint, g, jsonify, session

from api_helpers import json_object, login_required, password_byte_length, user_payload
from models import User


sessions = Blueprint("sessions", __name__)


@sessions.post("/login")
def login():
    data = json_object()
    if data is None:
        return jsonify({"error": "A JSON object is required"}), 400
    username, password = data.get("username"), data.get("password")
    if not isinstance(username, str) or not isinstance(password, str):
        return jsonify({"error": "Username and password are required"}), 400
    length = password_byte_length(password)
    if length is None or length > 72:
        return jsonify({"error": "Password must be at most 72 UTF-8 bytes"}), 400

    user = User.query.filter_by(username=username.strip().lower()).first()
    if user is None or not user.check_password(password):
        return jsonify({"error": "Invalid username or password"}), 401
    session.clear()
    session["user_id"] = user.id
    return jsonify(user_payload(user)), 200


@sessions.post("/logout")
def logout():
    session.clear()
    return "", 204


@sessions.get("/check_session")
@sessions.get("/me")
@login_required
def check_session():
    return jsonify(user_payload(g.current_user)), 200
