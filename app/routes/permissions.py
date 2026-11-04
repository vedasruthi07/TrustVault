from flask import Blueprint, request, jsonify, abort

from app.models import db, Document, User
from app.security import get_current_user
from app import limiter
from app.permission_management import (
    grant_document_permission,
    revoke_document_permission
)

permissions_bp = Blueprint("permissions", __name__, url_prefix="/api")


@permissions_bp.route(
    "/documents/<int:document_id>/permissions",
    methods=["POST"]
)
@limiter.limit("30 per hour")
def grant_permission(document_id):
    current_user = get_current_user()

    if current_user is None:
        abort(401)

    document = db.session.get(Document, document_id)

    if document is None:
        abort(404)

    data = request.get_json(silent=True) or {}

    if not data.get("username") or not data.get("permission"):
        return jsonify({
            "error": "Username and permission are required"
        }), 400

    target_user = User.query.filter_by(
        username=data.get("username")
    ).first()

    try:
        permission = grant_document_permission(
            current_user,
            document,
            target_user,
            data.get("permission")
        )

        return jsonify({
            "message": "Permission granted successfully",
            "username": target_user.username,
            "permission": permission.permission_level
        }), 200

    except PermissionError:
        abort(403)

    except ValueError as error:
        return jsonify({"error": str(error)}), 400


@permissions_bp.route(
    "/documents/<int:document_id>/permissions/<int:user_id>",
    methods=["DELETE"]
)
def revoke_permission(document_id, user_id):
    current_user = get_current_user()

    if current_user is None:
        abort(401)

    document = db.session.get(Document, document_id)

    if document is None:
        abort(404)

    target_user = db.session.get(User, user_id)

    if target_user is None:
        abort(404)

    try:
        result = revoke_document_permission(
            current_user,
            document,
            target_user
        )

        if not result:
            return jsonify({
                "message": "No permission found"
            }), 404

        return jsonify({
            "message": "Permission revoked successfully"
        }), 200

    except PermissionError:
        abort(403)

    except ValueError as error:
        return jsonify({"error": str(error)}), 400