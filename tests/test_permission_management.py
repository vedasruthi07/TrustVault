import pytest
from flask import Flask

from app.models import db, User, Document, DocumentPermission
from app.permission_management import (
    grant_document_permission,
    revoke_document_permission
)


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "test-secret-key"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()

        owner = User(
            username="owner",
            email="owner@example.com",
            role="OWNER"
        )
        owner.set_password("OwnerPassword123!")

        reader = User(
            username="reader",
            email="reader@example.com",
            role="VIEWER"
        )
        reader.set_password("ReaderPassword123!")

        stranger = User(
            username="stranger",
            email="stranger@example.com",
            role="VIEWER"
        )
        stranger.set_password("StrangerPassword123!")

        db.session.add_all([owner, reader, stranger])
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

        yield app

        db.session.remove()
        db.drop_all()


def test_owner_can_grant_read_permission(app):
    with app.app_context():
        owner = User.query.filter_by(username="owner").first()
        reader = User.query.filter_by(username="reader").first()
        document = Document.query.first()

        permission = grant_document_permission(
            owner, document, reader, "READ"
        )

        assert permission.permission_level == "READ"


def test_owner_can_update_permission(app):
    with app.app_context():
        owner = User.query.filter_by(username="owner").first()
        reader = User.query.filter_by(username="reader").first()
        document = Document.query.first()

        grant_document_permission(owner, document, reader, "READ")
        permission = grant_document_permission(
            owner, document, reader, "EDIT"
        )

        assert permission.permission_level == "EDIT"

        count = DocumentPermission.query.filter_by(
            document_id=document.id,
            user_id=reader.id
        ).count()

        assert count == 1


def test_non_owner_cannot_grant_permission(app):
    with app.app_context():
        stranger = User.query.filter_by(username="stranger").first()
        reader = User.query.filter_by(username="reader").first()
        document = Document.query.first()

        with pytest.raises(PermissionError):
            grant_document_permission(
                stranger, document, reader, "READ"
            )


def test_invalid_permission_is_rejected(app):
    with app.app_context():
        owner = User.query.filter_by(username="owner").first()
        reader = User.query.filter_by(username="reader").first()
        document = Document.query.first()

        with pytest.raises(ValueError):
            grant_document_permission(
                owner, document, reader, "DELETE"
            )


def test_owner_can_revoke_permission(app):
    with app.app_context():
        owner = User.query.filter_by(username="owner").first()
        reader = User.query.filter_by(username="reader").first()
        document = Document.query.first()

        grant_document_permission(owner, document, reader, "READ")

        result = revoke_document_permission(
            owner, document, reader
        )

        assert result is True
        assert DocumentPermission.query.count() == 0


def test_non_owner_cannot_revoke_permission(app):
    with app.app_context():
        owner = User.query.filter_by(username="owner").first()
        stranger = User.query.filter_by(username="stranger").first()
        reader = User.query.filter_by(username="reader").first()
        document = Document.query.first()

        grant_document_permission(owner, document, reader, "READ")

        with pytest.raises(PermissionError):
            revoke_document_permission(
                stranger, document, reader
            )


def test_revoking_nonexistent_permission(app):
    with app.app_context():
        owner = User.query.filter_by(username="owner").first()
        reader = User.query.filter_by(username="reader").first()
        document = Document.query.first()

        result = revoke_document_permission(
            owner, document, reader
        )

        assert result is False