
import pytest

from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "test-secret-key"
    app.config["RATELIMIT_STORAGE_URI"] = "memory://"

    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=[],
        storage_uri="memory://"
    )

    limiter.init_app(app)

    @app.route("/limited")
    @limiter.limit("3 per minute")
    def limited_route():
        return {"message": "Request allowed"}, 200

    return app


@pytest.fixture
def client(app):
    return app.test_client()


def test_requests_within_limit_are_allowed(client):
    for _ in range(3):
        response = client.get("/limited")
        assert response.status_code == 200


def test_requests_exceeding_limit_are_rejected(client):
    for _ in range(3):
        client.get("/limited")

    response = client.get("/limited")

    assert response.status_code == 429
