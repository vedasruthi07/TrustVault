
from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, session
)
from sqlalchemy.exc import IntegrityError

from app.models import db, User
from app.audit import log_activity
from app import limiter


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not username or not email or not password:
            flash("Please fill in all required fields.", "danger")
            return render_template("register.html")

        if len(username) > 80 or len(email) > 120:
            flash("Username or email is too long.", "danger")
            return render_template("register.html")

        if len(password) < 12:
            flash("Password must contain at least 12 characters.", "danger")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("register.html")

        existing_user = User.query.filter(
            (User.username == username) |
            (User.email == email)
        ).first()

        if existing_user:
            flash("Username or email is already registered.", "danger")
            return render_template("register.html")

        user = User(
            username=username,
            email=email,
            role="OWNER",
            is_active=True
        )

        user.set_password(password)

        try:
            db.session.add(user)
            db.session.flush()

            log_activity(
                action="REGISTER",
                outcome="SUCCESS",
                actor=user,
                details="New owner account registered",
                commit=False
            )

            db.session.commit()

        except IntegrityError:
            db.session.rollback()
            flash("Username or email is already registered.", "danger")
            return render_template("register.html")

        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])
def login():

    if request.method == "POST":

        identity = request.form.get("identity", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter(
            (User.username == identity) |
            (User.email == identity.lower())
        ).first()

        if user is None or not user.is_active or not user.check_password(password):

            log_activity(
                action="LOGIN",
                outcome="DENIED",
                details="Invalid login attempt"
            )

            flash("Invalid username/email or password.", "danger")
            return render_template("login.html")

        session.clear()
        session["user_id"] = user.id

        log_activity(
            action="LOGIN",
            outcome="SUCCESS",
            actor=user,
            details="User logged in"
        )

        flash("Login successful.", "success")
        return redirect("/")

    return render_template("login.html")


@auth_bp.route("/logout", methods=["POST"])
def logout():

    user_id = session.get("user_id")

    if user_id is not None:
        user = db.session.get(User, user_id)

        log_activity(
            action="LOGOUT",
            outcome="SUCCESS",
            actor=user,
            details="User logged out"
        )

    session.clear()

    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))
