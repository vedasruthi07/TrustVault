
import pytest

from flask import Flask

from app.models import db, User, Document, DocumentPermission, AuditLog
from app.routes.documents import documents_bp


@pytest.fixture
def app(tmp_path):
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "test-secret-key"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["UPLOAD_FOLDER"] = str(tmp_path)

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


def test_owner_can_edit_document(client, app):
    login(client, 1)

    response = client.patch(
        "/api/documents/1",
        json={"title": "Updated Document"}
    )

    assert response.status_code == 200

    with app.app_context():
        document = db.session.get(Document, 1)
        assert document.title == "Updated Document"

        audit = AuditLog.query.filter_by(
            action="DOCUMENT_EDIT",
            outcome="SUCCESS"
        ).first()
        assert audit is not None


def test_reader_cannot_edit_document(client):
    login(client, 2)

    response = client.patch(
        "/api/documents/1",
        json={"title": "Unauthorized Change"}
    )

    assert response.status_code == 403


def test_stranger_cannot_delete_document(client):
    login(client, 3)

    response = client.delete("/api/documents/1")

    assert response.status_code == 403


def test_owner_can_delete_document(client, app, tmp_path):
    login(client, 1)

    response = client.delete("/api/documents/1")

    assert response.status_code == 200

    with app.app_context():
        document = db.session.get(Document, 1)
        assert document is not None
        assert document.is_deleted is True

        audit = AuditLog.query.filter_by(
            action="DOCUMENT_DELETE",
            outcome="SUCCESS"
        ).first()
        assert audit is not None

    assert not (tmp_path / "test-file.pdf").exists()


def test_deleted_document_cannot_be_viewed(client, app):
    login(client, 1)

    with app.app_context():
        document = db.session.get(Document, 1)
        document.is_deleted = True
        db.session.commit()

    response = client.get("/api/documents/1/view")

    assert response.status_code == 404


def test_invalid_edit_is_rejected(client):
    login(client, 1)

    response = client.patch(
        "/api/documents/1",
        json={"title": ""}
    )

    assert response.status_code == 400
