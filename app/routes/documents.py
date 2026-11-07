
import os
import uuid
from pathlib import Path
from datetime import date

import pymupdf

from flask import (
    Blueprint,
    request,
    jsonify,
    current_app,
    abort,
    send_file
)

from sqlalchemy import or_
from werkzeug.utils import secure_filename

from app import limiter
from app.models import db, Document, DocumentPermission, User
from app.security import get_current_user
from app.audit import log_activity
from app.document_access import authorize_document_action


documents_bp = Blueprint(
    "documents",
    __name__,
    url_prefix="/api/documents"
)


# --------------------------------------------------
# 1. DOCUMENT UPLOAD
# --------------------------------------------------

@documents_bp.route("/upload", methods=["POST"])
@limiter.limit("10 per hour")
def upload_document():

    current_user = get_current_user()

    if current_user is None:
        log_activity(
            action="DOCUMENT_UPLOAD",
            outcome="DENIED",
            details="Unauthenticated upload attempt"
        )
        abort(401)

    uploaded_file = request.files.get("file")

    if uploaded_file is None or not uploaded_file.filename:
        return jsonify({
            "error": "Please select a PDF file"
        }), 400

    original_filename = secure_filename(
        uploaded_file.filename
    )

    if (
        not original_filename
        or not original_filename.lower().endswith(".pdf")
    ):
        log_activity(
            action="DOCUMENT_UPLOAD",
            outcome="DENIED",
            actor=current_user,
            details="Invalid file extension"
        )

        return jsonify({
            "error": "Only PDF files are allowed"
        }), 400

    max_size = current_app.config["MAX_CONTENT_LENGTH"]

    file_data = uploaded_file.stream.read(max_size + 1)

    if len(file_data) > max_size:
        log_activity(
            action="DOCUMENT_UPLOAD",
            outcome="DENIED",
            actor=current_user,
            details="File size limit exceeded"
        )

        return jsonify({
            "error": "File size exceeds the allowed limit"
        }), 413

    # Validate actual PDF structure.
    try:
        with pymupdf.open(
            stream=file_data,
            filetype="pdf"
        ) as pdf:

            if pdf.is_encrypted:
                raise ValueError(
                    "Encrypted PDF files are not allowed"
                )

            if len(pdf) == 0:
                raise ValueError(
                    "Empty PDF files are not allowed"
                )

    except Exception:
        log_activity(
            action="DOCUMENT_UPLOAD",
            outcome="DENIED",
            actor=current_user,
            details="Invalid, corrupted, encrypted or empty PDF"
        )

        return jsonify({
            "error": "Invalid, corrupted, encrypted or empty PDF"
        }), 400

    title = request.form.get("title", "").strip()

    if not title:
        title = Path(original_filename).stem

    if len(title) > 150:
        return jsonify({
            "error": "Title must be 150 characters or fewer"
        }), 400

    category = request.form.get("category", "").strip() or None

    if category and len(category) > 80:
        return jsonify({
            "error": "Category must be 80 characters or fewer"
        }), 400

    stored_filename = f"{uuid.uuid4().hex}.pdf"

    upload_folder = current_app.config["UPLOAD_FOLDER"]

    file_path = os.path.join(
        upload_folder,
        stored_filename
    )

    document = Document(
        title=title,
        original_filename=original_filename,
        stored_filename=stored_filename,
        category=category,
        file_size=len(file_data),
        mime_type="application/pdf",
        owner_id=current_user.id
    )

    try:
        with open(file_path, "xb") as file:
            file.write(file_data)

        db.session.add(document)
        db.session.flush()

        log_activity(
            action="DOCUMENT_UPLOAD",
            outcome="SUCCESS",
            actor=current_user,
            document=document,
            details="PDF document uploaded",
            commit=False
        )

        db.session.commit()

    except Exception:
        db.session.rollback()

        if os.path.exists(file_path):
            os.remove(file_path)

        current_app.logger.exception(
            "Document upload failed"
        )

        return jsonify({
            "error": "Document upload failed"
        }), 500

    return jsonify({
        "message": "Document uploaded successfully",
        "document": {
            "id": document.id,
            "title": document.title,
            "filename": document.original_filename,
            "category": document.category,
            "size": document.file_size
        }
    }), 201


# --------------------------------------------------
# 2. DOCUMENT VIEW AND DOWNLOAD
# --------------------------------------------------

def serve_document(document_id, as_attachment):

    current_user = get_current_user()

    document = db.session.get(
        Document,
        document_id
    )

    if document is None or document.is_deleted:
        abort(404)

    action = (
        "DOCUMENT_DOWNLOAD"
        if as_attachment
        else "DOCUMENT_VIEW"
    )

    if current_user is None:
        try:
            authorize_document_action(
                None,
                document,
                "READ",
                action
            )
        except PermissionError:
            abort(401)

    try:
        authorize_document_action(
            current_user,
            document,
            "READ",
            action
        )

    except PermissionError:
        abort(403)

    upload_folder = Path(
        current_app.config["UPLOAD_FOLDER"]
    ).resolve()

    file_path = (
        upload_folder / document.stored_filename
    ).resolve()

    # Prevent access outside private storage.
    if file_path.parent != upload_folder:
        abort(404)

    if not file_path.is_file():
        abort(404)

    return send_file(
        file_path,
        mimetype="application/pdf",
        as_attachment=as_attachment,
        download_name=document.original_filename,
        conditional=True
    )


@documents_bp.route(
    "/<int:document_id>/view",
    methods=["GET"]
)
def view_document(document_id):

    return serve_document(
        document_id,
        as_attachment=False
    )


@documents_bp.route(
    "/<int:document_id>/download",
    methods=["GET"]
)
def download_document(document_id):

    return serve_document(
        document_id,
        as_attachment=True
    )


# --------------------------------------------------
# 3. DOCUMENT EDIT
# --------------------------------------------------

@documents_bp.route(
    "/<int:document_id>",
    methods=["PATCH"]
)
def edit_document(document_id):

    current_user = get_current_user()

    if current_user is None:
        abort(401)

    document = db.session.get(
        Document,
        document_id
    )

    if document is None or document.is_deleted:
        abort(404)

    try:
        authorize_document_action(
            current_user,
            document,
            "EDIT",
            "DOCUMENT_EDIT"
        )

    except PermissionError:
        abort(403)

    data = request.get_json(silent=True) or {}

    title = data.get("title")
    category = data.get("category")

    if title is not None:

        if not isinstance(title, str) or not title.strip():
            return jsonify({
                "error": "Invalid title"
            }), 400

        if len(title.strip()) > 150:
            return jsonify({
                "error": "Title is too long"
            }), 400

    if category is not None:

        if (
            not isinstance(category, str)
            or len(category.strip()) > 80
        ):
            return jsonify({
                "error": "Invalid category"
            }), 400

    if title is None and category is None:
        return jsonify({
            "error": "No changes provided"
        }), 400

    try:
        if title is not None:
            document.title = title.strip()

        if category is not None:
            document.category = category.strip() or None

        log_activity(
            action="DOCUMENT_EDIT",
            outcome="SUCCESS",
            actor=current_user,
            document=document,
            details="Document metadata updated",
            commit=False
        )

        db.session.commit()

    except Exception:
        db.session.rollback()

        current_app.logger.exception(
            "Document edit failed"
        )

        return jsonify({
            "error": "Document update failed"
        }), 500

    return jsonify({
        "message": "Document updated successfully"
    }), 200


# --------------------------------------------------
# 4. DOCUMENT DELETE
# --------------------------------------------------

@documents_bp.route(
    "/<int:document_id>",
    methods=["DELETE"]
)
def delete_document(document_id):

    current_user = get_current_user()

    if current_user is None:
        abort(401)

    document = db.session.get(
        Document,
        document_id
    )

    if document is None or document.is_deleted:
        abort(404)

    try:
        authorize_document_action(
            current_user,
            document,
            "EDIT",
            "DOCUMENT_DELETE"
        )

    except PermissionError:
        abort(403)

    try:
        document.is_deleted = True

        log_activity(
            action="DOCUMENT_DELETE",
            outcome="SUCCESS",
            actor=current_user,
            document=document,
            details="Document soft-deleted",
            commit=False
        )

        db.session.commit()

    except Exception:
        db.session.rollback()

        current_app.logger.exception(
            "Document deletion failed"
        )

        return jsonify({
            "error": "Document deletion failed"
        }), 500

    # Remove the private file after database commit.
    upload_folder = Path(
        current_app.config["UPLOAD_FOLDER"]
    ).resolve()

    file_path = (
        upload_folder / document.stored_filename
    ).resolve()

    if file_path.parent == upload_folder and file_path.is_file():

        try:
            file_path.unlink()

        except OSError:
            current_app.logger.exception(
                "Deleted document file could not be removed"
            )

    return jsonify({
        "message": "Document deleted successfully"
    }), 200


# --------------------------------------------------
# 5. DOCUMENT SEARCH
# --------------------------------------------------

@documents_bp.route(
    "/search",
    methods=["GET"]
)
def search_documents():

    current_user = get_current_user()

    if current_user is None:
        abort(401)

    # Get owned documents and documents shared with the user.
    shared_document_ids = db.session.query(
        DocumentPermission.document_id
    ).filter(
        DocumentPermission.user_id == current_user.id
    )

    query = Document.query.filter(
        Document.is_deleted.is_(False),
        or_(
            Document.owner_id == current_user.id,
            Document.id.in_(shared_document_ids)
        )
    )

    # Search by title.
    title = request.args.get(
        "title",
        ""
    ).strip()

    if title:
        query = query.filter(
            Document.title.ilike(f"%{title}%")
        )

    # Search by owner username.
    owner = request.args.get(
        "owner",
        ""
    ).strip()

    if owner:
        query = query.filter(
            Document.owner.has(
                User.username.ilike(f"%{owner}%")
            )
        )

    # Search by category.
    category = request.args.get(
        "category",
        ""
    ).strip()

    if category:
        query = query.filter(
            Document.category.ilike(f"%{category}%")
        )

    # Search by date range.
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")

    try:
        parsed_from = None
        parsed_to = None

        if date_from:
            parsed_from = date.fromisoformat(date_from)

            query = query.filter(
                db.func.date(Document.created_at)
                >= parsed_from.isoformat()
            )

        if date_to:
            parsed_to = date.fromisoformat(date_to)

            query = query.filter(
                db.func.date(Document.created_at)
                <= parsed_to.isoformat()
            )

        if (
            parsed_from is not None
            and parsed_to is not None
            and parsed_from > parsed_to
        ):
            return jsonify({
                "error": "Invalid date range"
            }), 400

    except ValueError:
        return jsonify({
            "error": "Dates must use YYYY-MM-DD format"
        }), 400

    documents = query.order_by(
        Document.created_at.desc()
    ).limit(100).all()

    results = []

    for document in documents:

        # Determine this user's permission.
        if document.owner_id == current_user.id:
            permission_level = "OWNER"

        else:
            document_permission = DocumentPermission.query.filter_by(
                document_id=document.id,
                user_id=current_user.id
            ).first()

            permission_level = (
                document_permission.permission_level
                if document_permission else None
            )

        results.append({
            "id": document.id,
            "title": document.title,
            "filename": document.original_filename,
            "category": document.category,
            "owner": document.owner.username,
            "permission": permission_level,
            "created_at": (
                document.created_at.isoformat()
                if document.created_at else None
            )
        })

    return jsonify({
        "count": len(results),
        "documents": results
    }), 200
