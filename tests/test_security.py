import pytest
from flask import Flask, session
from werkzeug.exceptions import Unauthorized, Forbidden

from app.models import db, User
from app.security import get_current_user, require_role


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "test-secret-key"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()

        user = User(
            username="testuser",
            email="test@example.com",
            role="OWNER"
        )
        user.set_password("TestPassword123!")

        db.session.add(user)
        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()


def test_get_current_user(app):
    with app.test_request_context():
        session["user_id"] = 1

        user = get_current_user()

        assert user is not None
        assert user.username == "testuser"


def test_inactive_user_is_rejected(app):
    with app.app_context():
        user = db.session.get(User, 1)
        user.is_active = False
        db.session.commit()

    with app.test_request_context():
        session["user_id"] = 1

        assert get_current_user() is None
        assert "user_id" not in session


def test_unauthenticated_user_is_rejected(app):
    @require_role("ADMIN")
    def protected_view():
        return "Allowed"

    with app.test_request_context():
        with pytest.raises(Unauthorized):
            protected_view()


def test_wrong_role_is_rejected(app):
    @require_role("ADMIN")
    def protected_view():
        return "Allowed"

    with app.test_request_context():
        session["user_id"] = 1

        with pytest.raises(Forbidden):
            protected_view()