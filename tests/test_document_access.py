import pytest
from flask import Flask

from app.models import db, User, Document, AuditLog, DocumentPermission
from app.document_access import authorize_document_action


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

        reader = User(
            username="reader",
            email="reader@example.com",
            role="VIEWER"
        )

        editor = User(
            username="editor",
            email="editor@example.com",
            role="VIEWER"
        )

        stranger = User(
            username="stranger",
            email="stranger@example.com",
            role="VIEWER"
        )

        owner.set_password("OwnerPassword123!")
        reader.set_password("ReaderPassword123!")
        editor.set_password("EditorPassword123!")
        stranger.set_password("StrangerPassword123!")

        db.session.add_all([owner, reader, editor, stranger])
        db.session.commit()
        document = Document(
            title="Test Document",
            original_filename="test.pdf",
            stored_filename="test-file.pdf",
            category="Personal",
            file_size=1024,
            mime_type="application/pdf",
            owner_id=owner.id
        )

        db.session.add(document)
        db.session.commit()

        db.session.add_all([
            DocumentPermission(
                document_id=document.id,
                user_id=reader.id,
                permission_level="READ",
                granted_by_id=owner.id
            ),
            DocumentPermission(
                document_id=document.id,
                user_id=editor.id,
                permission_level="EDIT",
                granted_by_id=owner.id
            )
        ])

        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()


def test_owner_can_read_and_edit(app):
    with app.app_context():
        owner = User.query.filter_by(username="owner").first()
        document = Document.query.first()

        assert authorize_document_action(
            owner, document, "READ", "DOCUMENT_VIEW"
        ) is True

        assert authorize_document_action(
            owner, document, "EDIT", "DOCUMENT_EDIT"
        ) is True


def test_reader_cannot_edit(app):
    with app.app_context():
        reader = User.query.filter_by(username="reader").first()
        document = Document.query.first()

        with pytest.raises(PermissionError):
            authorize_document_action(
                reader, document, "EDIT", "DOCUMENT_EDIT"
            )

        log = AuditLog.query.filter_by(
            action="DOCUMENT_EDIT",
            outcome="DENIED"
        ).first()

        assert log is not None


def test_stranger_cannot_read(app):
    with app.app_context():
        stranger = User.query.filter_by(username="stranger").first()
        document = Document.query.first()

        with pytest.raises(PermissionError):
            authorize_document_action(
                stranger, document, "READ", "DOCUMENT_VIEW"
            )

        log = AuditLog.query.filter_by(
            action="DOCUMENT_VIEW",
            outcome="DENIED"
        ).first()

        assert log is not None


def test_editor_can_read_and_edit(app):
    with app.app_context():
        editor = User.query.filter_by(username="editor").first()
        document = Document.query.first()

        assert authorize_document_action(
            editor, document, "READ", "DOCUMENT_VIEW"
        ) is True

        assert authorize_document_action(
            editor, document, "EDIT", "DOCUMENT_EDIT"
        ) is True


def test_revoked_reader_is_denied(app):
    with app.app_context():
        reader = User.query.filter_by(username="reader").first()
        document = Document.query.first()

        permission = DocumentPermission.query.filter_by(
            document_id=document.id,
            user_id=reader.id
        ).first()

        db.session.delete(permission)
        db.session.commit()

        with pytest.raises(PermissionError):
            authorize_document_action(
                reader, document, "READ", "DOCUMENT_VIEW"
            )


def test_invalid_permission_requirement(app):
    with app.app_context():
        owner = User.query.filter_by(username="owner").first()
        document = Document.query.first()

        with pytest.raises(ValueError):
            authorize_document_action(
                owner, document, "DELETE", "DOCUMENT_DELETE"
            )
def test_unauthenticated_access_is_denied_and_audited(app):
    with app.app_context():
        document = Document.query.first()

        with pytest.raises(PermissionError):
            authorize_document_action(
                None,
                document,
                "READ",
                "DOCUMENT_VIEW"
            )

        log = AuditLog.query.filter_by(
            action="DOCUMENT_VIEW",
            outcome="DENIED"
        ).first()

        assert log is not None
        assert log.actor_id is None
        assert log.document_id == document.id
        assert log.details == "Unauthenticated access attempt"