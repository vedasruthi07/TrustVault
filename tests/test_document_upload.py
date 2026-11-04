
import io
import pytest
import pymupdf

from flask import Flask

from app.models import db, User, Document, AuditLog
from app.routes.documents import documents_bp


def create_valid_pdf():
    """Create a genuine PDF for upload testing."""
    pdf = pymupdf.open()

    page = pdf.new_page()
    page.insert_text(
        (72, 72),
        "TrustVault test document"
    )

    file_data = pdf.tobytes()
    pdf.close()

    return file_data


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

        owner.set_password("OwnerPassword123!")

        db.session.add(owner)
        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def login(client):
    with client.session_transaction() as session:
        session["user_id"] = 1


def test_authenticated_user_can_upload_pdf(client, app):
    login(client)

    response = client.post(
        "/api/documents/upload",
        data={
            "file": (
                io.BytesIO(create_valid_pdf()),
                "sample.pdf"
            ),
            "title": "My Document",
            "category": "Personal"
        },
        content_type="multipart/form-data"
    )

    assert response.status_code == 201

    with app.app_context():
        document = Document.query.first()

        assert document is not None
        assert document.title == "My Document"
        assert document.owner_id == 1

        audit = AuditLog.query.filter_by(
            action="DOCUMENT_UPLOAD",
            outcome="SUCCESS"
        ).first()

        assert audit is not None
        assert audit.document_id == document.id


def test_unauthenticated_upload_is_rejected(client):
    response = client.post(
        "/api/documents/upload",
        data={
            "file": (
                io.BytesIO(create_valid_pdf()),
                "sample.pdf"
            )
        },
        content_type="multipart/form-data"
    )

    assert response.status_code == 401


def test_non_pdf_extension_is_rejected(client):
    login(client)

    response = client.post(
        "/api/documents/upload",
        data={
            "file": (
                io.BytesIO(b"some text"),
                "sample.txt"
            )
        },
        content_type="multipart/form-data"
    )

    assert response.status_code == 400


def test_invalid_pdf_signature_is_rejected(client):
    login(client)

    response = client.post(
        "/api/documents/upload",
        data={
            "file": (
                io.BytesIO(b"not a real PDF"),
                "sample.pdf"
            )
        },
        content_type="multipart/form-data"
    )

    assert response.status_code == 400


def test_empty_upload_is_rejected(client):
    login(client)

    response = client.post(
        "/api/documents/upload",
        data={},
        content_type="multipart/form-data"
    )

    assert response.status_code == 400
