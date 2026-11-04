import pytest
from flask import Flask

from app.models import db, User, Document, AuditLog
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
            stored_filename="test.pdf",
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


def test_grant_permission_creates_audit_record(app):
    with app.app_context():
        owner = User.query.filter_by(username="owner").first()
        reader = User.query.filter_by(username="reader").first()
        document = Document.query.first()

        grant_document_permission(owner, document, reader, "READ")

        log = AuditLog.query.filter_by(
            action="PERMISSION_GRANT"
        ).first()

        assert log is not None
        assert log.outcome == "SUCCESS"
        assert log.actor_id == owner.id
        assert log.document_id == document.id


def test_revoke_permission_creates_audit_record(app):
    with app.app_context():
        owner = User.query.filter_by(username="owner").first()
        reader = User.query.filter_by(username="reader").first()
        document = Document.query.first()

        grant_document_permission(owner, document, reader, "READ")
        revoke_document_permission(owner, document, reader)

        logs = AuditLog.query.filter_by(
            action="PERMISSION_REVOKE"
        ).all()

        assert len(logs) == 1
        assert logs[0].outcome == "SUCCESS"


def test_denied_grant_creates_audit_record(app):
    with app.app_context():
        stranger = User.query.filter_by(username="stranger").first()
        reader = User.query.filter_by(username="reader").first()
        document = Document.query.first()

        with pytest.raises(PermissionError):
            grant_document_permission(
                stranger, document, reader, "READ"
            )

        log = AuditLog.query.filter_by(
            action="PERMISSION_GRANT",
            outcome="DENIED"
        ).first()

        assert log is not None
        assert log.actor_id == stranger.id