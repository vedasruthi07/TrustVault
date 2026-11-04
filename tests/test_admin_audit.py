
import pytest

from flask import Flask

from app.models import db, User, AuditLog
from app.routes.admin import admin_bp


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "test-secret-key"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    app.register_blueprint(admin_bp)

    with app.app_context():
        db.create_all()

        admin = User(
            username="admin",
            email="admin@example.com",
            role="ADMIN"
        )
        owner = User(
            username="owner",
            email="owner@example.com",
            role="OWNER"
        )

        admin.set_password("AdminPassword123!")
        owner.set_password("OwnerPassword123!")

        db.session.add_all([admin, owner])
        db.session.commit()

        db.session.add_all([
            AuditLog(
                actor_id=owner.id,
                document_id=1,
                action="DOCUMENT_UPLOAD",
                outcome="SUCCESS",
                details="PDF uploaded"
            ),
            AuditLog(
                actor_id=owner.id,
                document_id=1,
                action="PERMISSION_GRANT",
                outcome="DENIED",
                details="Unauthorized permission attempt"
            )
        ])
        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def login(client, user_id):
    with client.session_transaction() as session:
        session["user_id"] = user_id


def test_admin_can_view_audit_logs(client):
    login(client, 1)

    response = client.get("/api/admin/audit-logs")

    assert response.status_code == 200
    assert response.json["total"] == 2
    assert len(response.json["audit_logs"]) == 2


def test_non_admin_cannot_view_audit_logs(client):
    login(client, 2)

    response = client.get("/api/admin/audit-logs")

    assert response.status_code == 403


def test_unauthenticated_user_cannot_view_audit_logs(client):
    response = client.get("/api/admin/audit-logs")

    assert response.status_code == 401


def test_admin_can_filter_denied_actions(client):
    login(client, 1)

    response = client.get(
        "/api/admin/audit-logs?outcome=DENIED"
    )

    assert response.status_code == 200
    assert response.json["total"] == 1
    assert response.json["audit_logs"][0]["outcome"] == "DENIED"


def test_admin_can_filter_by_action(client):
    login(client, 1)

    response = client.get(
        "/api/admin/audit-logs?action=DOCUMENT_UPLOAD"
    )

    assert response.status_code == 200
    assert response.json["total"] == 1
    assert response.json["audit_logs"][0]["action"] == "DOCUMENT_UPLOAD"


def test_invalid_outcome_is_rejected(client):
    login(client, 1)

    response = client.get(
        "/api/admin/audit-logs?outcome=UNKNOWN"
    )

    assert response.status_code == 400


def test_admin_response_does_not_expose_document_contents(client):
    login(client, 1)

    response = client.get("/api/admin/audit-logs")

    assert response.status_code == 200

    record = response.json["audit_logs"][0]

    assert "document_id" in record
    assert "file_path" not in record
    assert "file_content" not in record
    assert "stored_filename" not in record
