
import os
from flask import Flask
from dotenv import load_dotenv
from app.models import db


def create_app():
    load_dotenv()

    from config import Config

    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)

    with app.app_context():
        db.create_all()

    return app
