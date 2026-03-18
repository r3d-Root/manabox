from functools import wraps
from flask import Blueprint, render_template, session, redirect, url_for
from app.services.importer import get_collection_table, fetch_all_rows

web_bp = Blueprint("web", __name__)

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user" not in session:
            return render_template(
                "collection.html",
                user=None,
                columns=[],
                rows=[],
            )
        return view(*args, **kwargs)
    return wrapped

@web_bp.route("/")
@login_required
def index():
    table = get_collection_table()
    if table is None:
        return render_template(
            "collection.html",
            user=session.get("user"),
            columns=[],
            rows=[],
        )

    columns = [col.name for col in table.columns if col.name != "id"]
    raw_rows = fetch_all_rows(table)

    rows = []
    for row in raw_rows:
        data = row._mapping
        rows.append([data.get(col, "") for col in columns])

    return render_template(
        "collection.html",
        user=session.get("user"),
        columns=columns,
        rows=rows,
    )