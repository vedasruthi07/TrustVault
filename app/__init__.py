
import os

from flask import Flask, jsonify
from dotenv import load_dotenv
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect, CSRFError, generate_csrf
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from app.models import db

migrate = Migrate()
csrf = CSRFProtect()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=os.environ.get(
        "RATELIMIT_STORAGE_URI",
        "memory://"
    )
)


def register_error_handlers(app):

    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({"error": "Authentication required"}), 401

    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({"error": "Access denied"}), 403

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(413)
    def file_too_large(error):
        return jsonify({"error": "File size exceeds the allowed limit"}), 413

    @app.errorhandler(CSRFError)
    def csrf_error(error):
        return jsonify({
            "error": "CSRF validation failed",
            "reason": error.description
        }), 400
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        return {
        "error": "Too many requests. Please try again later."
    }, 429


def create_app():
    load_dotenv()

    from config import Config

    app = Flask(__name__)
    app.config.from_object(Config)

    app.config["WTF_CSRF_ENABLED"] = True
    app.config["WTF_CSRF_HEADERS"] = [
        "X-CSRFToken",
        "X-CSRF-Token"
    ]

    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    limiter.init_app(app)

    from app.routes.permissions import permissions_bp
    from app.routes.documents import documents_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(permissions_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(admin_bp)

    @app.route("/api/csrf-token", methods=["GET"])
    def get_csrf_token():
        return jsonify({
            "csrf_token": generate_csrf()
        }), 200

    register_error_handlers(app)

    return app
