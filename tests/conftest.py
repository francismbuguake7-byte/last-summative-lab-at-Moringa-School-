import pytest
from sqlalchemy import create_engine

from app import app
from models import db


@pytest.fixture(autouse=True)
def reset_database():
    app.config.update(TESTING=True, SECRET_KEY="test-secret")
    with app.app_context():
        original_engine = db.engines[None]
        test_engine = create_engine("sqlite:///:memory:")
        db.engines[None] = test_engine
    try:
        with app.app_context():
            db.session.remove()
            db.drop_all()
            db.create_all()
        yield
    finally:
        with app.app_context():
            db.session.remove()
            db.drop_all()
            db.engines[None] = original_engine
        test_engine.dispose()


@pytest.fixture
def client():
    return app.test_client()
