import pytest
from flask import Flask

from app.models import db, User, AuditLog
from app.audit import log_activity


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "test-secret-key"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()

        user = User(
            username="testuser",
            email="test@example.com",
            role="OWNER"
        )
        user.set_password("TestPassword123!")

        db.session.add(user)
        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()


def test_successful_activity_is_logged(app):
    with app.app_context():
        user = User.query.first()

        entry = log_activity(
            action="DOCUMENT_UPLOAD",
            outcome="SUCCESS",
            actor=user,
            details="Test upload"
        )

        assert entry.action == "DOCUMENT_UPLOAD"
        assert entry.outcome == "SUCCESS"
        assert entry.actor_id == user.id
        assert entry.entry_hash is not None


def test_denied_activity_is_logged(app):
    with app.app_context():
        user = User.query.first()

        entry = log_activity(
            action="DOCUMENT_ACCESS",
            outcome="DENIED",
            actor=user,
            details="Access denied"
        )

        assert entry.outcome == "DENIED"
        assert entry.details == "Access denied"


def test_audit_entries_form_hash_chain(app):
    with app.app_context():
        user = User.query.first()

        first = log_activity(
            action="DOCUMENT_UPLOAD",
            outcome="SUCCESS",
            actor=user
        )

        second = log_activity(
            action="DOCUMENT_DOWNLOAD",
            outcome="SUCCESS",
            actor=user
        )

        assert first.previous_hash is None
        assert second.previous_hash == first.entry_hash
        assert second.entry_hash != first.entry_hash


def test_invalid_outcome_is_rejected(app):
    with app.app_context():
        user = User.query.first()

        with pytest.raises(ValueError):
            log_activity(
                action="DOCUMENT_DELETE",
                outcome="INVALID",
                actor=user
            )
def test_audit_chain_detects_modified_record(app):
    from app.audit import verify_audit_chain

    with app.app_context():
        user = User.query.first()

        log_activity(
            action="DOCUMENT_UPLOAD",
            outcome="SUCCESS",
            actor=user,
            details="Original record"
        )

        assert verify_audit_chain() is True

        entry = AuditLog.query.first()
        entry.details = "Modified record"
        db.session.commit()

        assert verify_audit_chain() is False


def test_audit_chain_detects_deleted_record(app):
    from app.audit import verify_audit_chain

    with app.app_context():
        user = User.query.first()

        log_activity(
            action="DOCUMENT_UPLOAD",
            outcome="SUCCESS",
            actor=user
        )

        log_activity(
            action="DOCUMENT_DOWNLOAD",
            outcome="SUCCESS",
            actor=user
        )

        assert verify_audit_chain() is True

        first_entry = AuditLog.query.order_by(AuditLog.id.asc()).first()
        db.session.delete(first_entry)
        db.session.commit()

        assert verify_audit_chain() is False