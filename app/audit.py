import hashlib
import hmac
import json

from datetime import datetime, timezone
from flask import current_app, request, has_request_context

from app.models import db, AuditLog


def create_entry_hash(audit_data):
    payload = json.dumps(
        audit_data,
        sort_keys=True,
        separators=(",", ":")
    ).encode("utf-8")

    secret_key = current_app.config["SECRET_KEY"].encode("utf-8")

    return hmac.new(
        secret_key,
        payload,
        hashlib.sha256
    ).hexdigest()


def log_activity(
    action,
    outcome,
    actor=None,
    document=None,
    details=None,
    commit=True
):
    if outcome not in ("SUCCESS", "DENIED"):
        raise ValueError("Invalid audit outcome.")

    previous_entry = AuditLog.query.order_by(
        AuditLog.id.desc()
    ).first()

    previous_hash = (
        previous_entry.entry_hash if previous_entry else None
    )

    created_at = datetime.now(timezone.utc)

    audit_data = {
        "actor_id": actor.id if actor else None,
        "document_id": document.id if document else None,
        "action": action,
        "outcome": outcome,
        "details": details,
        "ip_address": (
            request.remote_addr if has_request_context() else None
        ),
        "created_at": created_at.isoformat(),
        "previous_hash": previous_hash
    }

    entry_hash = create_entry_hash(audit_data)

    entry = AuditLog(
        actor_id=audit_data["actor_id"],
        document_id=audit_data["document_id"],
        action=action,
        outcome=outcome,
        details=details,
        ip_address=audit_data["ip_address"],
        created_at=created_at,
        previous_hash=previous_hash,
        entry_hash=entry_hash
    )

    db.session.add(entry)

    if commit:
        db.session.commit()
    else:
        db.session.flush()

    return entry


def verify_audit_chain():
    entries = AuditLog.query.order_by(AuditLog.id.asc()).all()

    expected_previous_hash = None

    for entry in entries:

        if entry.previous_hash != expected_previous_hash:
            return False

        created_at = entry.created_at

        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        else:
            created_at = created_at.astimezone(timezone.utc)

        audit_data = {
            "actor_id": entry.actor_id,
            "document_id": entry.document_id,
            "action": entry.action,
            "outcome": entry.outcome,
            "details": entry.details,
            "ip_address": entry.ip_address,
            "created_at": created_at.isoformat(),
            "previous_hash": entry.previous_hash
        }

        calculated_hash = create_entry_hash(audit_data)

        if not hmac.compare_digest(
            calculated_hash,
            entry.entry_hash or ""
        ):
            return False

        expected_previous_hash = entry.entry_hash

    return True