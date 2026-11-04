from app.models import db, DocumentPermission
from app.audit import log_activity


def grant_document_permission(
    actor,
    document,
    target_user,
    permission_level
):
    # Only the document owner can grant access
    if document.owner_id != actor.id:
        log_activity(
            action="PERMISSION_GRANT",
            outcome="DENIED",
            actor=actor,
            document=document,
            details="Non-owner attempted to grant access"
        )
        raise PermissionError("Only the document owner can grant access.")

    # Validate permission level
    if permission_level not in ("READ", "EDIT"):
        log_activity(
            action="PERMISSION_GRANT",
            outcome="DENIED",
            actor=actor,
            document=document,
            details="Invalid permission level"
        )
        raise ValueError("Permission must be READ or EDIT.")

    # Validate target user
    if target_user is None or not target_user.is_active:
        log_activity(
            action="PERMISSION_GRANT",
            outcome="DENIED",
            actor=actor,
            document=document,
            details="Invalid or inactive target user"
        )
        raise ValueError("Target user is invalid or inactive.")

    if target_user.id == actor.id:
        raise ValueError("Owner already has full access.")

    permission = DocumentPermission.query.filter_by(
        document_id=document.id,
        user_id=target_user.id
    ).first()

    if permission:
        permission.permission_level = permission_level
        action_details = "Existing permission updated"
    else:
        permission = DocumentPermission(
            document_id=document.id,
            user_id=target_user.id,
            permission_level=permission_level,
            granted_by_id=actor.id
        )
        db.session.add(permission)
        action_details = "New permission granted"

    db.session.commit()

    log_activity(
        action="PERMISSION_GRANT",
        outcome="SUCCESS",
        actor=actor,
        document=document,
        details=action_details
    )

    return permission


def revoke_document_permission(actor, document, target_user):
    # Only the document owner can revoke access
    if document.owner_id != actor.id:
        log_activity(
            action="PERMISSION_REVOKE",
            outcome="DENIED",
            actor=actor,
            document=document,
            details="Non-owner attempted to revoke access"
        )
        raise PermissionError("Only the document owner can revoke access.")

    if target_user is None:
        log_activity(
            action="PERMISSION_REVOKE",
            outcome="DENIED",
            actor=actor,
            document=document,
            details="Invalid target user"
        )
        raise ValueError("Target user is invalid.")

    permission = DocumentPermission.query.filter_by(
        document_id=document.id,
        user_id=target_user.id
    ).first()

    if permission is None:
        log_activity(
            action="PERMISSION_REVOKE",
            outcome="SUCCESS",
            actor=actor,
            document=document,
            details="No existing permission to revoke"
        )
        return False

    db.session.delete(permission)
    db.session.commit()

    log_activity(
        action="PERMISSION_REVOKE",
        outcome="SUCCESS",
        actor=actor,
        document=document,
        details="Document permission revoked"
    )

    return True