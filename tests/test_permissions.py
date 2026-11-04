import pytest

from app.models import db, User, Document, DocumentPermission
from app.permissions import (
    get_document_permission,
    can_read_document,
    can_edit_document
)


@pytest.fixture
def app():
    app = __import__("flask").Flask(__name__)
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

        editor = User(
            username="editor",
            email="editor@example.com",
            role="VIEWER"
        )
        editor.set_password("EditorPassword123!")

        stranger = User(
            username="stranger",
            email="stranger@example.com",
            role="VIEWER"
        )
        stranger.set_password("StrangerPassword123!")

        db.session.add_all([owner, reader, editor, stranger])
        db.session.commit()

        document = Document(
            title="Test Document",
            original_filename="test.pdf",
            stored_filename="unique-test-file.pdf",
            category="Personal",
            file_size=1024,
            mime_type="application/pdf",
            owner_id=owner.id
        )

        db.session.add(document)
        db.session.commit()

        reader_permission = DocumentPermission(
            document_id=document.id,
            user_id=reader.id,
            permission_level="READ",
            granted_by_id=owner.id
        )

        editor_permission = DocumentPermission(
            document_id=document.id,
            user_id=editor.id,
            permission_level="EDIT",
            granted_by_id=owner.id
        )

        db.session.add_all([reader_permission, editor_permission])
        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()


def test_owner_can_read_and_edit(app):
    with app.app_context():
        owner = User.query.filter_by(username="owner").first()
        document = Document.query.first()

        assert can_read_document(owner, document) is True
        assert can_edit_document(owner, document) is True


def test_reader_can_only_read(app):
    with app.app_context():
        reader = User.query.filter_by(username="reader").first()
        document = Document.query.first()

        assert can_read_document(reader, document) is True
        assert can_edit_document(reader, document) is False


def test_editor_can_read_and_edit(app):
    with app.app_context():
        editor = User.query.filter_by(username="editor").first()
        document = Document.query.first()

        assert can_read_document(editor, document) is True
        assert can_edit_document(editor, document) is True


def test_user_without_permission_is_denied(app):
    with app.app_context():
        stranger = User.query.filter_by(username="stranger").first()
        document = Document.query.first()

        assert get_document_permission(stranger, document) is None
        assert can_read_document(stranger, document) is False
        assert can_edit_document(stranger, document) is False


def test_revoked_permission_is_denied(app):
    with app.app_context():
        reader = User.query.filter_by(username="reader").first()
        document = Document.query.first()

        assert can_read_document(reader, document) is True

        permission = DocumentPermission.query.filter_by(
            document_id=document.id,
            user_id=reader.id
        ).first()

        db.session.delete(permission)
        db.session.commit()

        assert can_read_document(reader, document) is False
        assert can_edit_document(reader, document) is False