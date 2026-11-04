import os
from flask import Flask
from dotenv import load_dotenv
from flask_migrate import Migrate
from app.models import db

migrate = Migrate()


def create_app():
    load_dotenv()

    from config import Config

    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)

    return app