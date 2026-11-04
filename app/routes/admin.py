
from flask import Blueprint, request, jsonify

from app.models import db, AuditLog, User
from app.security import require_role


admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/api/admin"
)


@admin_bp.route("/audit-logs", methods=["GET"])
@require_role("ADMIN")
def get_audit_logs():

    action = request.args.get("action", "").strip()
    outcome = request.args.get("outcome", "").strip().upper()

    try:
        limit = min(max(int(request.args.get("limit", 50)), 1), 100)
        offset = max(int(request.args.get("offset", 0)), 0)
    except ValueError:
        return jsonify({"error": "Invalid pagination values"}), 400

    if outcome and outcome not in ("SUCCESS", "DENIED"):
        return jsonify({"error": "Invalid audit outcome"}), 400

    query = db.session.query(
        AuditLog,
        User.username
    ).outerjoin(
        User,
        AuditLog.actor_id == User.id
    )

    if action:
        query = query.filter(AuditLog.action == action)

    if outcome:
        query = query.filter(AuditLog.outcome == outcome)

    total = query.count()

    records = query.order_by(
        AuditLog.id.desc()
    ).offset(offset).limit(limit).all()

    results = []

    for log, username in records:
        results.append({
            "id": log.id,
            "actor_id": log.actor_id,
            "actor_username": username,
            "document_id": log.document_id,
            "action": log.action,
            "outcome": log.outcome,
            "details": log.details,
            "ip_address": log.ip_address,
            "created_at": (
                log.created_at.isoformat()
                if log.created_at else None
            )
        })

    return jsonify({
        "total": total,
        "limit": limit,
        "offset": offset,
        "audit_logs": results
    }), 200
