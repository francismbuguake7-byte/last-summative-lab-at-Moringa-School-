import os
from functools import wraps
from pathlib import Path

from flask import Flask, g, jsonify, request, session
from flask_cors import CORS
from flask_migrate import Migrate
from sqlalchemy.exc import IntegrityError

from models import Event, User, bcrypt, db


app = Flask(__name__)
Path(app.instance_path).mkdir(parents=True, exist_ok=True)
secret_key = os.environ.get("SECRET_KEY")
if not secret_key and os.environ.get("FLASK_ENV") == "production":
    raise RuntimeError("SECRET_KEY must be configured in production")

app.config.update(
    SECRET_KEY=secret_key or "dev-only-change-this-secret-key",
    SQLALCHEMY_DATABASE_URI=os.environ.get(
        "DATABASE_URL", f"sqlite:///{Path(app.instance_path) / 'productivity.db'}"
    ),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "false").lower() == "true",
    CORS_ORIGINS=os.environ.get("CORS_ORIGINS", "http://localhost:3000"),
)

CORS(
    app,
    origins=[
        origin.strip()
        for origin in app.config["CORS_ORIGINS"].split(",")
        if origin.strip()
    ],
    supports_credentials=True,
)
db.init_app(app)
bcrypt.init_app(app)
migrate = Migrate(app, db)


def json_object():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None
    return data


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


@app.post("/signup")
def signup():
    data = json_object()
    if data is None:
        return jsonify({"error": "A JSON object is required"}), 400

    username = data.get("username")
    password = data.get("password")
    if not isinstance(username, str) or not isinstance(password, str):
        return jsonify({"error": "Username and password are required"}), 400

    username = username.strip().lower()
    if not 3 <= len(username) <= 80:
        return jsonify({"error": "Username must be between 3 and 80 characters"}), 400
    password_length = password_byte_length(password)
    if password_length is None or not 8 <= password_length <= 72:
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


@app.post("/login")
def login():
    data = json_object()
    if data is None:
        return jsonify({"error": "A JSON object is required"}), 400

    username = data.get("username")
    password = data.get("password")
    if not isinstance(username, str) or not isinstance(password, str):
        return jsonify({"error": "Username and password are required"}), 400
    password_length = password_byte_length(password)
    if password_length is None or password_length > 72:
        return jsonify({"error": "Password must be at most 72 UTF-8 bytes"}), 400

    user = User.query.filter_by(username=username.strip().lower()).first()
    if user is None or not user.check_password(password):
        return jsonify({"error": "Invalid username or password"}), 401

    session.clear()
    session["user_id"] = user.id
    return jsonify(user_payload(user)), 200


@app.post("/logout")
def logout():
    session.clear()
    return "", 204


@app.get("/check_session")
@app.get("/me")
@login_required
def check_session():
    return jsonify(user_payload(g.current_user)), 200


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


@app.get("/events")
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


@app.post("/events")
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


@app.patch("/events/<int:event_id>")
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
            value = data[field].strip()
            setattr(event, field, value)
    db.session.commit()
    return jsonify(event_payload(event)), 200


@app.delete("/events/<int:event_id>")
@login_required
def delete_event(event_id):
    event = Event.query.filter_by(id=event_id, user_id=g.current_user.id).first()
    if event is None:
        return jsonify({"error": "Event not found"}), 404

    db.session.delete(event)
    db.session.commit()
    return "", 204


if __name__ == "__main__":
    app.run()
