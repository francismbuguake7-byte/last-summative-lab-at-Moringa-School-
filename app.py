import os
from pathlib import Path

from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate

from auth_routes import auth
from event_read_routes import event_reads
from event_write_routes import event_writes
from models import bcrypt, db
from session_routes import sessions

migrate = Migrate()


def create_app():
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
        SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "false").lower()
        == "true",
        CORS_ORIGINS=os.environ.get("CORS_ORIGINS", "http://localhost:3000"),
    )
    origins = [
        origin.strip()
        for origin in app.config["CORS_ORIGINS"].split(",")
        if origin.strip()
    ]
    CORS(app, origins=origins, supports_credentials=True)
    db.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)
    app.register_blueprint(auth)
    app.register_blueprint(sessions)
    app.register_blueprint(event_reads)
    app.register_blueprint(event_writes)
    return app


app = create_app()

if __name__ == "__main__":
    app.run()
