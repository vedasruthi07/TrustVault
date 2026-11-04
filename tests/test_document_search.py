
import pytest
from datetime import date

from flask import Flask

from app.models import db, User, Document, DocumentPermission
from app.routes.documents import documents_bp


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "test-secret-key"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["UPLOAD_FOLDER"] = "private_uploads"

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

        for user, password in [
            (owner, "OwnerPassword123!"),
            (reader, "ReaderPassword123!"),
            (stranger, "StrangerPassword123!")
        ]:
            user.set_password(password)

        db.session.add_all([owner, reader, stranger])
        db.session.commit()

        document1 = Document(
            title="Annual Report",
            original_filename="report.pdf",
            stored_filename="report-file.pdf",
            category="Finance",
            file_size=100,
            mime_type="application/pdf",
            owner_id=owner.id
        )

        document2 = Document(
            title="Personal Notes",
            original_filename="notes.pdf",
            stored_filename="notes-file.pdf",
            category="Personal",
            file_size=200,
            mime_type="application/pdf",
            owner_id=owner.id
        )

        db.session.add_all([document1, document2])
        db.session.commit()

        permission = DocumentPermission(
            document_id=document1.id,
            user_id=reader.id,
            permission_level="READ",
            granted_by_id=owner.id
        )

        db.session.add(permission)
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


def test_unauthenticated_search_is_rejected(client):
    response = client.get("/api/documents/search")
    assert response.status_code == 401


def test_owner_sees_own_documents(client):
    login(client, 1)

    response = client.get("/api/documents/search")

    assert response.status_code == 200
    assert response.json["count"] == 2


def test_reader_sees_only_shared_documents(client):
    login(client, 2)

    response = client.get("/api/documents/search")

    assert response.status_code == 200
    assert response.json["count"] == 1
    assert response.json["documents"][0]["title"] == "Annual Report"


def test_stranger_cannot_see_other_users_documents(client):
    login(client, 3)

    response = client.get("/api/documents/search")

    assert response.status_code == 200
    assert response.json["count"] == 0


def test_search_by_title_and_category(client):
    login(client, 1)

    response = client.get(
        "/api/documents/search?title=annual&category=finance"
    )

    assert response.status_code == 200
    assert response.json["count"] == 1
    assert response.json["documents"][0]["title"] == "Annual Report"


def test_search_by_owner(client):
    login(client, 2)

    response = client.get(
        "/api/documents/search?owner=owner"
    )

    assert response.status_code == 200
    assert response.json["count"] == 1


def test_search_by_date(client):
    login(client, 1)

    today = date.today().isoformat()

    response = client.get(
        f"/api/documents/search?date_from={today}&date_to={today}"
    )

    assert response.status_code == 200
    assert response.json["count"] == 2


def test_invalid_date_is_rejected(client):
    login(client, 1)

    response = client.get(
        "/api/documents/search?date_from=invalid-date"
    )

    assert response.status_code == 400


def test_reversed_date_range_is_rejected(client):
    login(client, 1)

    response = client.get(
        "/api/documents/search?date_from=2026-11-04&date_to=2026-11-01"
    )

    assert response.status_code == 400
