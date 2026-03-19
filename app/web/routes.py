from functools import wraps
from flask import Blueprint, render_template, session
from sqlalchemy import text
from app.extensions import db

web_bp = Blueprint("web", __name__)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user" not in session:
            return render_template("collection.html", user=None, cards=[])
        return view(*args, **kwargs)
    return wrapped


@web_bp.route("/")
@login_required
def index():
    sql = text("""
        SELECT
            c.scryfall_id,
            c.quantity,
            c.foil,
            c.condition,
            c.language,
            s.name,
            s.set_code,
            s.set_name,
            s.collector_number,
            s.rarity,
            s.mana_cost,
            s.type_line,
            s.image_small,
            s.scryfall_uri
        FROM collection_items c
        LEFT JOIN scryfall_cards s
            ON c.scryfall_id = s.scryfall_id
        ORDER BY s.name ASC, c.condition ASC
    """)

    with db.engine.begin() as conn:
        cards = conn.execute(sql).mappings().all()

    return render_template(
        "collection.html",
        user=session.get("user"),
        cards=cards,
    )