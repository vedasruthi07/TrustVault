
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")

    if not SECRET_KEY:
        raise RuntimeError("SECRET_KEY is not configured.")

    SQLALCHEMY_DATABASE_URI = (
        f"sqlite:///{BASE_DIR / 'instance' / 'trustvault.db'}"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAX_CONTENT_LENGTH = 10 * 1024 * 1024

    UPLOAD_FOLDER = str(BASE_DIR / "private_uploads")

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = (
    os.environ.get("APP_ENV", "development").lower() == "production"
)
