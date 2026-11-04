from app.models import db, Document, DocumentPermission


def get_document_permission(user, document):
    # Document owner has full access
    if document.owner_id == user.id:
        return "OWNER"

    # Check whether the user has an explicit permission
    permission = DocumentPermission.query.filter_by(
        document_id=document.id,
        user_id=user.id
    ).first()

    if permission is None:
        return None

    return permission.permission_level


def can_read_document(user, document):
    permission = get_document_permission(user, document)

    return permission in ("OWNER", "READ", "EDIT")


def can_edit_document(user, document):
    permission = get_document_permission(user, document)

    return permission in ("OWNER", "EDIT")