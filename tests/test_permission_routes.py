import pytest
from flask import Flask

from app.models import db, User, Document, DocumentPermission, AuditLog
from app.routes.permissions import permissions_bp


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "test-secret-key"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.register_blueprint(permissions_bp)

    db.init_app(app)

    with app.app_context():
        db.create_all()

        owner = User(
            username="owner",
            email="owner@example.com",
            role="OWNER"
        )
        owner.set_password("OwnerPassword123!")

        viewer = User(
            username="viewer",
            email="viewer@example.com",
            role="VIEWER"
        )
        viewer.set_password("ViewerPassword123!")

        stranger = User(
            username="stranger",
            email="stranger@example.com",
            role="VIEWER"
        )
        stranger.set_password("StrangerPassword123!")

        db.session.add_all([owner, viewer, stranger])
        db.session.commit()

        document = Document(
            title="Test Document",
            original_filename="test.pdf",
            stored_filename="test-document.pdf",
            category="Personal",
            file_size=1024,
            mime_type="application/pdf",
            owner_id=owner.id
        )

        db.session.add(document)
        db.session.commit()

        app.config["TEST_IDS"] = {
            "owner": owner.id,
            "viewer": viewer.id,
            "stranger": stranger.id,
            "document": document.id
        }

        yield app

        db.session.remove()
        db.drop_all()


def login_as(client, user_id):
    with client.session_transaction() as session:
        session["user_id"] = user_id


def test_unauthenticated_user_cannot_grant_permission(app):
    client = app.test_client()
    document_id = app.config["TEST_IDS"]["document"]

    response = client.post(
        f"/api/documents/{document_id}/permissions",
        json={
            "username": "viewer",
            "permission": "READ"
        }
    )

    assert response.status_code == 401


def test_owner_can_grant_permission(app):
    client = app.test_client()
    ids = app.config["TEST_IDS"]

    login_as(client, ids["owner"])

    response = client.post(
        f"/api/documents/{ids['document']}/permissions",
        json={
            "username": "viewer",
            "permission": "READ"
        }
    )

    assert response.status_code == 200
    assert response.json["permission"] == "READ"


def test_non_owner_cannot_grant_permission(app):
    client = app.test_client()
    ids = app.config["TEST_IDS"]

    login_as(client, ids["stranger"])

    response = client.post(
        f"/api/documents/{ids['document']}/permissions",
        json={
            "username": "viewer",
            "permission": "READ"
        }
    )

    assert response.status_code == 403


def test_owner_can_revoke_permission(app):
    client = app.test_client()
    ids = app.config["TEST_IDS"]

    login_as(client, ids["owner"])

    client.post(
        f"/api/documents/{ids['document']}/permissions",
        json={
            "username": "viewer",
            "permission": "READ"
        }
    )

    response = client.delete(
        f"/api/documents/{ids['document']}/permissions/{ids['viewer']}"
    )

    assert response.status_code == 200


def test_missing_permission_data_is_rejected(app):
    client = app.test_client()
    ids = app.config["TEST_IDS"]

    login_as(client, ids["owner"])

    response = client.post(
        f"/api/documents/{ids['document']}/permissions",
        json={}
    )

    assert response.status_code == 400