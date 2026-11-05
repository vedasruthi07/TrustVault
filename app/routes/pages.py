
from flask import Blueprint, render_template, redirect, url_for

from app.security import get_current_user


pages_bp = Blueprint("pages", __name__)


@pages_bp.route("/")
def home():

    user = get_current_user()

    if user is None:
        return redirect(url_for("auth.login"))

    return render_template("dashboard.html", current_user=user)
