from flask import Blueprint, jsonify, session
from sqlalchemy.exc import IntegrityError

from api_helpers import json_object, password_byte_length, user_payload
from models import User, db


auth = Blueprint("auth", __name__)


@auth.post("/signup")
def signup():
    data = json_object()
    if data is None:
        return jsonify({"error": "A JSON object is required"}), 400
    username, password = data.get("username"), data.get("password")
    if not isinstance(username, str) or not isinstance(password, str):
        return jsonify({"error": "Username and password are required"}), 400

    username = username.strip().lower()
    length = password_byte_length(password)
    if not 3 <= len(username) <= 80:
        return jsonify({"error": "Username must be between 3 and 80 characters"}), 400
    if length is None or not 8 <= length <= 72:
        return jsonify({"error": "Password must be between 8 and 72 bytes"}), 400
    if User.query.filter_by(username=username).first() is not None:
        return jsonify({"error": "Username is already taken"}), 409

    user = User(username=username)
    user.set_password(password)
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Username is already taken"}), 409

    session.clear()
    session["user_id"] = user.id
    return jsonify(user_payload(user)), 201
