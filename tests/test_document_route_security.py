
import io
import pytest
import pymupdf
from app.routes.permissions import permissions_bp

from flask import Flask

from app.models import (
    db,
    User,
    Document,
    DocumentPermission,
    AuditLog
)
from app.routes.documents import documents_bp


def create_pdf():
    pdf = pymupdf.open()
    page = pdf.new_page()
    page.insert_text((72, 72), "TrustVault security test")
    content = pdf.tobytes()
    pdf.close()
    return content


@pytest.fixture
def app(tmp_path):
    app = Flask(__name__)

    app.config.update(
        SECRET_KEY="test-secret-key",
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        UPLOAD_FOLDER=str(tmp_path),
        MAX_CONTENT_LENGTH=10 * 1024 * 1024
    )

    db.init_app(app)

    app.register_blueprint(documents_bp)
    app.register_blueprint(permissions_bp)

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

        pdf_content = create_pdf()

        document = Document(
            title="Private Document",
            original_filename="private.pdf",
            stored_filename="private-test.pdf",
            category="Testing",
            file_size=len(pdf_content),
            mime_type="application/pdf",
            owner_id=owner.id
        )

        db.session.add(document)
        db.session.commit()

        with open(
            tmp_path / "private-test.pdf",
            "wb"
        ) as file:
            file.write(pdf_content)

        app.config["TEST_OWNER_ID"] = owner.id
        app.config["TEST_VIEWER_ID"] = viewer.id
        app.config["TEST_STRANGER_ID"] = stranger.id
        app.config["TEST_DOCUMENT_ID"] = document.id

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def login_as(client, user_id):
    with client.session_transaction() as session:
        session["user_id"] = user_id


def test_owner_can_view_and_download_document(client, app):
    login_as(client, app.config["TEST_OWNER_ID"])

    document_id = app.config["TEST_DOCUMENT_ID"]

    view_response = client.get(
        f"/api/documents/{document_id}/view"
    )

    download_response = client.get(
        f"/api/documents/{document_id}/download"
    )

    assert view_response.status_code == 200
    assert download_response.status_code == 200


def test_stranger_cannot_view_or_download_document(client, app):
    login_as(client, app.config["TEST_STRANGER_ID"])

    document_id = app.config["TEST_DOCUMENT_ID"]

    view_response = client.get(
        f"/api/documents/{document_id}/view"
    )

    download_response = client.get(
        f"/api/documents/{document_id}/download"
    )

    assert view_response.status_code == 403
    assert download_response.status_code == 403


def test_stranger_cannot_edit_document(client, app):
    login_as(client, app.config["TEST_STRANGER_ID"])

    document_id = app.config["TEST_DOCUMENT_ID"]

    response = client.patch(
        f"/api/documents/{document_id}",
        json={"title": "Unauthorized Change"}
    )

    assert response.status_code == 403

    with app.app_context():
        document = db.session.get(
            Document,
            document_id
        )

        assert document.title == "Private Document"


def test_stranger_cannot_delete_document(client, app):
    login_as(client, app.config["TEST_STRANGER_ID"])

    document_id = app.config["TEST_DOCUMENT_ID"]

    response = client.delete(
        f"/api/documents/{document_id}"
    )

    assert response.status_code == 403

    with app.app_context():
        document = db.session.get(
            Document,
            document_id
        )

        assert document is not None
        assert document.is_deleted is False


def test_viewer_with_read_permission_can_view(client, app):
    document_id = app.config["TEST_DOCUMENT_ID"]
    viewer_id = app.config["TEST_VIEWER_ID"]
    owner_id = app.config["TEST_OWNER_ID"]

    with app.app_context():
        permission = DocumentPermission(
            document_id=document_id,
            user_id=viewer_id,
            permission_level="READ",
            granted_by_id=owner_id
        )

        db.session.add(permission)
        db.session.commit()

    login_as(client, viewer_id)

    response = client.get(
        f"/api/documents/{document_id}/view"
    )

    assert response.status_code == 200


def test_read_only_viewer_cannot_edit_or_delete(client, app):
    document_id = app.config["TEST_DOCUMENT_ID"]
    viewer_id = app.config["TEST_VIEWER_ID"]
    owner_id = app.config["TEST_OWNER_ID"]

    with app.app_context():
        permission = DocumentPermission(
            document_id=document_id,
            user_id=viewer_id,
            permission_level="READ",
            granted_by_id=owner_id
        )

        db.session.add(permission)
        db.session.commit()

    login_as(client, viewer_id)

    edit_response = client.patch(
        f"/api/documents/{document_id}",
        json={"title": "Unauthorized Change"}
    )

    delete_response = client.delete(
        f"/api/documents/{document_id}"
    )

    assert edit_response.status_code == 403
    assert delete_response.status_code == 403

    with app.app_context():
        document = db.session.get(
            Document,
            document_id
        )

        assert document.title == "Private Document"
        assert document.is_deleted is False

def test_revoked_permission_immediately_blocks_document_access(client, app):
    document_id = app.config["TEST_DOCUMENT_ID"]
    owner_id = app.config["TEST_OWNER_ID"]
    viewer_id = app.config["TEST_VIEWER_ID"]

    # Owner grants READ permission.
    login_as(client, owner_id)

    grant_response = client.post(
        f"/api/documents/{document_id}/permissions",
        json={
            "username": "viewer",
            "permission": "READ"
        }
    )

    assert grant_response.status_code == 200

    # Viewer can access the document.
    login_as(client, viewer_id)

    view_response = client.get(
        f"/api/documents/{document_id}/view"
    )

    assert view_response.status_code == 200

    # Owner revokes the viewer's permission.
    login_as(client, owner_id)

    revoke_response = client.delete(
        f"/api/documents/{document_id}/permissions/{viewer_id}"
    )

    assert revoke_response.status_code == 200

    # The viewer must lose access on the very next request.
    login_as(client, viewer_id)

    blocked_response = client.get(
        f"/api/documents/{document_id}/view"
    )

    assert blocked_response.status_code == 403

def test_failed_upload_leaves_no_file_or_database_record(
    client, app, monkeypatch
):
    import io
    from app.models import db, Document
    from app.routes.documents import upload_document

    login_as(client, app.config["TEST_OWNER_ID"])

    def fail_commit():
        raise RuntimeError("Simulated database failure")

    with app.app_context():
        monkeypatch.setattr(db.session(), "commit", fail_commit)

        response = client.post(
            "/api/documents/upload",
            data={
                "file": (
                    io.BytesIO(create_pdf()),
                    "failure-test.pdf"
                ),
                "title": "Failed Upload"
            },
            content_type="multipart/form-data"
        )

        assert response.status_code == 500

        documents = Document.query.filter_by(
            title="Failed Upload"
        ).all()

        assert len(documents) == 0

        files = list(
            (app.config["UPLOAD_FOLDER"] and
             __import__("pathlib").Path(
                 app.config["UPLOAD_FOLDER"]
             )).glob("*")
        )

        assert not any(
            file.name.endswith(".pdf")
            and file.name != "private-test.pdf"
            for file in files
        )


def test_failed_edit_rolls_back_database_changes(
    client, app, monkeypatch
):
    from app.models import db, Document

    login_as(client, app.config["TEST_OWNER_ID"])

    original_commit = db.session().commit
    commit_count = 0

    def fail_second_commit():
        nonlocal commit_count
        commit_count += 1

        if commit_count == 2:
            raise RuntimeError("Simulated database failure")

        return original_commit()

    with app.app_context():
        monkeypatch.setattr(
            db.session(),
            "commit",
            fail_second_commit
        )

        document_id = app.config["TEST_DOCUMENT_ID"]

        response = client.patch(
            f"/api/documents/{document_id}",
            json={"title": "Failed Edit"}
        )

        assert response.status_code == 500

        document = db.session.get(Document, document_id)

        assert document.title == "Private Document"


def test_failed_delete_keeps_document_and_file(
    client, app, monkeypatch
):
    from pathlib import Path
    from app.models import db, Document

    login_as(client, app.config["TEST_OWNER_ID"])

    original_commit = db.session().commit
    commit_count = 0

    def fail_second_commit():
        nonlocal commit_count
        commit_count += 1

        if commit_count == 2:
            raise RuntimeError("Simulated database failure")

        return original_commit()

    with app.app_context():
        monkeypatch.setattr(
            db.session(),
            "commit",
            fail_second_commit
        )

        document_id = app.config["TEST_DOCUMENT_ID"]

        response = client.delete(
            f"/api/documents/{document_id}"
        )

        assert response.status_code == 500

        document = db.session.get(Document, document_id)

        assert document is not None
        assert document.is_deleted is False

        file_path = (
            Path(app.config["UPLOAD_FOLDER"])
            / document.stored_filename
        )

        assert file_path.is_file()
