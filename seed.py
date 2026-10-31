from app import app
from models import Event, User, db


def seed():
    with app.app_context():
        demo_user = User.query.filter_by(username="demo").first()
        if demo_user is None:
            demo_user = User(username="demo")
            demo_user.set_password("DemoPass123!")
            db.session.add(demo_user)
            db.session.flush()
            db.session.add_all(
                [
                    Event(
                        title="Plan the week",
                        description="Choose three priorities for the week.",
                        user_id=demo_user.id,
                    ),
                    Event(
                        title="Take a screen break",
                        description="Step away from the desk for ten minutes.",
                        user_id=demo_user.id,
                    ),
                    Event(
                        title="Review progress",
                        description="Write down what went well today.",
                        user_id=demo_user.id,
                    ),
                ]
            )
            db.session.commit()
            print("Created demo user and sample events.")
        else:
            print("Demo user already exists; no seed data was changed.")


if __name__ == "__main__":
    seed()
