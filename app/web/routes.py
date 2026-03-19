from functools import wraps
from flask import Blueprint, render_template, session

web_bp = Blueprint("web", __name__)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user" not in session:
            return render_template("collection.html", user=None)
        return view(*args, **kwargs)
    return wrapped


@web_bp.route("/")
@login_required
def index():
    return render_template(
        "collection.html",
        user=session.get("user"),
    )