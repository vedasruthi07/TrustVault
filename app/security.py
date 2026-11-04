from functools import wraps
from flask import session, abort

from app.models import db, User


def get_current_user():
    user_id = session.get("user_id")

    if user_id is None:
        return None

    user = db.session.get(User, user_id)

    if user is None or not user.is_active:
        session.clear()
        return None

    return user


def require_role(*allowed_roles):
    def decorator(view_function):
        @wraps(view_function)
        def wrapped(*args, **kwargs):
            user = get_current_user()

            if user is None:
                abort(401)

            if user.role not in allowed_roles:
                abort(403)

            return view_function(*args, **kwargs)

        return wrapped

    return decorator