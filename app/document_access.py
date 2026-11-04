from app.permissions import (
    can_read_document,
    can_edit_document
)
from app.audit import log_activity


def authorize_document_action(
    user,
    document,
    required_permission,
    action
):
    # Validate requested permission
    if required_permission not in ("READ", "EDIT"):
        raise ValueError("Invalid permission requirement.")

    # Check whether the user is authenticated
    if user is None:
        log_activity(
            action=action,
            outcome="DENIED",
            document=document,
            details="Unauthenticated access attempt"
        )
        raise PermissionError("Authentication required.")

    # Check document-level authorization
    if required_permission == "READ":
        allowed = can_read_document(user, document)
    else:
        allowed = can_edit_document(user, document)

    # Record denied access
    if not allowed:
        log_activity(
            action=action,
            outcome="DENIED",
            actor=user,
            document=document,
            details="Insufficient document permission"
        )
        raise PermissionError("You are not authorized.")

    # Record successful access
    log_activity(
        action=action,
        outcome="SUCCESS",
        actor=user,
        document=document,
        details=f"{required_permission} permission verified"
    )

    return True