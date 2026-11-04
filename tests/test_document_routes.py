
import pytest

from flask import Flask

from app.models import (
    db, User, Document, DocumentPermission, AuditLog
)
from app.routes.documents import documents_bp


@pytest.fixture
def app(tmp_path):
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "test-secret-key"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["UPLOAD_FOLDER"] = str(tmp_path)
    app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

    db.init_app(app)
    app.register_blueprint(documents_bp)

    with app.app_context():
        db.create_all()

        owner = User(
            username="owner",
            email="owner@example.com",
            role="OWNER"
        )
        reader = User(
            username="reader",
            email="reader@example.com",
            role="VIEWER"
        )
        stranger = User(
            username="stranger",
            email="stranger@example.com",
            role="VIEWER"
        )

        owner.set_password("OwnerPassword123!")
        reader.set_password("ReaderPassword123!")
        stranger.set_password("StrangerPassword123!")

        db.session.add_all([owner, reader, stranger])
        db.session.commit()

        document = Document(
            title="Test Document",
            original_filename="test.pdf",
            stored_filename="test-file.pdf",
            category="Personal",
            file_size=25,
            mime_type="application/pdf",
            owner_id=owner.id
        )

        db.session.add(document)
        db.session.commit()

        permission = DocumentPermission(
            document_id=document.id,
            user_id=reader.id,
            permission_level="READ",
            granted_by_id=owner.id
        )

        db.session.add(permission)
        db.session.commit()

        (tmp_path / "test-file.pdf").write_bytes(
            b"%PDF-1.4 test PDF content"
        )

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def login(client, user_id):
    with client.session_transaction() as session:
        session["user_id"] = user_id


def test_owner_can_view_document(client):
    login(client, 1)

    response = client.get("/api/documents/1/view")

    assert response.status_code == 200
    assert response.data.startswith(b"%PDF-")


def test_reader_can_download_document(client):
    login(client, 2)

    response = client.get("/api/documents/1/download")

    assert response.status_code == 200
    assert response.data.startswith(b"%PDF-")
    assert "attachment" in response.headers["Content-Disposition"]


def test_stranger_cannot_view_document(client):
    login(client, 3)

    response = client.get("/api/documents/1/view")

    assert response.status_code == 403


def test_unauthenticated_user_cannot_download(client):
    response = client.get("/api/documents/1/download")

    assert response.status_code == 401


def test_revoked_reader_cannot_view_document(client, app):
    login(client, 2)

    with app.app_context():
        permission = DocumentPermission.query.filter_by(
            document_id=1,
            user_id=2
        ).first()

        db.session.delete(permission)
        db.session.commit()

    response = client.get("/api/documents/1/view")

    assert response.status_code == 403


def test_denied_view_is_recorded_in_audit_log(client, app):
    login(client, 3)

    response = client.get("/api/documents/1/view")

    assert response.status_code == 403

    with app.app_context():
        audit = AuditLog.query.filter_by(
            action="DOCUMENT_VIEW",
            outcome="DENIED"
        ).first()

        assert audit is not None
        assert audit.actor_id == 3
        assert audit.document_id == 1
