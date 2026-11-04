
import pytest

from app import create_app
from app.models import db


@pytest.fixture
def app(tmp_path):
    app = create_app()

    app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        UPLOAD_FOLDER=str(tmp_path)
    )

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def test_csrf_token_endpoint_returns_token(client):
    response = client.get("/api/csrf-token")

    assert response.status_code == 200
    assert "csrf_token" in response.json
    assert response.json["csrf_token"]


def test_post_without_csrf_token_is_rejected(client):
    response = client.post(
        "/api/documents/1/permissions",
        json={
            "username": "reader",
            "permission": "READ"
        }
    )

    assert response.status_code == 400
    assert response.json["error"] == "CSRF validation failed"


def test_post_with_invalid_csrf_token_is_rejected(client):
    response = client.post(
        "/api/documents/1/permissions",
        json={
            "username": "reader",
            "permission": "READ"
        },
        headers={
            "X-CSRFToken": "invalid-token"
        }
    )

    assert response.status_code == 400


@pytest.mark.parametrize(
    "method, path, content_type",
    [
        ("POST", "/api/documents/upload", "multipart/form-data"),
        ("PATCH", "/api/documents/1", "application/json"),
        ("DELETE", "/api/documents/1", None),
        ("POST", "/api/documents/1/permissions", "application/json"),
        ("DELETE", "/api/documents/1/permissions/2", None),
    ]
)
def test_actual_endpoints_reject_requests_without_csrf(
    client,
    method,
    path,
    content_type
):
    response = client.open(
        path,
        method=method,
        content_type=content_type
    )

    assert response.status_code == 400
    assert response.json["error"] == "CSRF validation failed"
