from flask import request, jsonify
from flask.views import MethodView
from flask_smorest import Blueprint
from sqlalchemy import select, func, inspect, text

from app.extensions import db
from app.models.sync_status import SyncStatus
from app.services.importer import get_collection_table
from .schemas import (
    HealthSchema,
    CollectionMetaSchema,
    SyncStatusSchema,
    FilterOptionsSchema,
    TableDataQuerySchema,
    TableDataResponseSchema,
)

api_bp = Blueprint("api", __name__, url_prefix="/api", description="ManaBox API")

FOIL_EXPR = """
CASE
    WHEN lower(trim(COALESCE(c.foil, ''))) IN ('true', '1', 'yes', 'foil')
    THEN 'Foil'
    ELSE 'Nonfoil'
END
"""

PRICE_EXPR = f"""
CASE
    WHEN lower(trim(COALESCE(c.foil, ''))) IN ('true', '1', 'yes', 'foil')
    THEN COALESCE(s.usd_foil, s.usd)
    ELSE COALESCE(s.usd, s.usd_foil)
END
"""

GROUPED_CTE = f"""
WITH grouped AS (
    SELECT
        c.scryfall_id AS scryfall_id,
        s.name AS name,
        UPPER(s.set_code) AS set_code,
        s.set_name AS set_name,
        s.rarity AS rarity,
        s.mana_cost AS mana_cost,
        s.type_line AS type_line,
        s.image_small AS image_small,
        s.image_normal AS image_normal,
        s.scryfall_uri AS scryfall_uri,
        {FOIL_EXPR} AS finish,
        SUM(CAST(COALESCE(NULLIF(c.quantity, ''), '0') AS INTEGER)) AS quantity,
        {PRICE_EXPR} AS avg_price
    FROM collection_items c
    LEFT JOIN scryfall_cards s
        ON c.scryfall_id = s.scryfall_id
    GROUP BY
        c.scryfall_id,
        s.name,
        s.set_code,
        s.set_name,
        s.rarity,
        s.mana_cost,
        s.type_line,
        s.image_small,
        s.image_normal,
        s.scryfall_uri,
        {FOIL_EXPR},
        {PRICE_EXPR}
)
"""


def has_collection_items():
    inspector = inspect(db.engine)
    return "collection_items" in inspector.get_table_names()


def build_filters(params):
    where_clauses = []
    binds = {}

    set_filter = (params.get("set_filter") or "").strip()
    rarity_filter = (params.get("rarity_filter") or "").strip()
    finish_filter = (params.get("finish_filter") or "").strip()
    search_value = (params.get("search[value]") or "").strip().lower()

    if set_filter:
        where_clauses.append("set_code = :set_filter")
        binds["set_filter"] = set_filter.upper()

    if rarity_filter:
        where_clauses.append("rarity = :rarity_filter")
        binds["rarity_filter"] = rarity_filter

    if finish_filter:
        where_clauses.append("finish = :finish_filter")
        binds["finish_filter"] = finish_filter

    if search_value:
        where_clauses.append("""
            (
                lower(COALESCE(name, '')) LIKE :search_value
                OR lower(COALESCE(set_code, '')) LIKE :search_value
                OR lower(COALESCE(set_name, '')) LIKE :search_value
                OR lower(COALESCE(rarity, '')) LIKE :search_value
                OR lower(COALESCE(type_line, '')) LIKE :search_value
                OR lower(COALESCE(mana_cost, '')) LIKE :search_value
            )
        """)
        binds["search_value"] = f"%{search_value}%"

    return where_clauses, binds


def resolve_order(params):
    column_index = params.get("order[0][column]", "1")
    direction = params.get("order[0][dir]", "asc").lower()

    if direction not in ("asc", "desc"):
        direction = "asc"

    order_map = {
        "0": "name",
        "1": "name",
        "2": "set_code",
        "3": "rarity",
        "4": "mana_cost",
        "5": "type_line",
        "6": "quantity",
        "7": "finish",
        "8": "CAST(avg_price AS REAL)",
    }

    order_sql = order_map.get(column_index, "name")
    return f"{order_sql} {direction}"


@api_bp.route("/health")
class HealthResource(MethodView):
    @api_bp.response(200, HealthSchema)
    def get(self):
        return {"status": "ok"}


@api_bp.route("/collection/meta")
class CollectionMetaResource(MethodView):
    @api_bp.response(200, CollectionMetaSchema)
    def get(self):
        table = get_collection_table()
        if table is None:
            return {"row_count": 0, "columns": []}

        with db.engine.begin() as conn:
            count = conn.execute(select(func.count()).select_from(table)).scalar_one()

        columns = [col.name for col in table.columns if col.name != "id"]
        return {"row_count": count, "columns": columns}


@api_bp.route("/sync-status")
class SyncStatusResource(MethodView):
    @api_bp.response(200, SyncStatusSchema)
    def get(self):
        status = SyncStatus.get_singleton()

        percent = 0.0
        if status.total_cards > 0:
            percent = round((status.processed_cards / status.total_cards) * 100, 2)

        return {
            "is_running": status.is_running,
            "total_cards": status.total_cards,
            "processed_cards": status.processed_cards,
            "current_scryfall_id": status.current_scryfall_id,
            "current_card_name": status.current_card_name,
            "last_error": status.last_error,
            "percent": percent,
        }


@api_bp.route("/filter-options")
class FilterOptionsResource(MethodView):
    @api_bp.response(200, FilterOptionsSchema)
    def get(self):
        if not has_collection_items():
            return {
                "sets": [],
                "rarities": [],
                "finishes": [],
            }

        with db.engine.begin() as conn:
            sets = conn.execute(text(
                GROUPED_CTE + """
                SELECT DISTINCT set_code
                FROM grouped
                WHERE set_code IS NOT NULL AND set_code != ''
                ORDER BY set_code
                """
            )).fetchall()

            rarities = conn.execute(text(
                GROUPED_CTE + """
                SELECT DISTINCT rarity
                FROM grouped
                WHERE rarity IS NOT NULL AND rarity != ''
                ORDER BY rarity
                """
            )).fetchall()

            finishes = conn.execute(text(
                GROUPED_CTE + """
                SELECT DISTINCT finish
                FROM grouped
                WHERE finish IS NOT NULL AND finish != ''
                ORDER BY finish
                """
            )).fetchall()

        return {
            "sets": [row[0] for row in sets],
            "rarities": [row[0] for row in rarities],
            "finishes": [row[0] for row in finishes],
        }


@api_bp.route("/table-data")
class TableDataResource(MethodView):
    @api_bp.arguments(TableDataQuerySchema, location="query")
    @api_bp.response(200, TableDataResponseSchema)
    def get(self, args):
        if not has_collection_items():
            return {
                "draw": int(args.get("draw", 1)),
                "recordsTotal": 0,
                "recordsFiltered": 0,
                "data": [],
            }

        draw = int(args.get("draw", 1))
        start = int(args.get("start", 0))
        length = int(args.get("length", 50))
        if length <= 0:
            length = 50

        where_clauses, binds = build_filters(request.args)
        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        order_sql = resolve_order(request.args)

        with db.engine.begin() as conn:
            records_total = conn.execute(text(
                GROUPED_CTE + "SELECT COUNT(*) FROM grouped"
            )).scalar_one()

            records_filtered = conn.execute(text(
                GROUPED_CTE + f"SELECT COUNT(*) FROM grouped {where_sql}"
            ), binds).scalar_one()

            query = text(
                GROUPED_CTE + f"""
                SELECT
                    scryfall_id,
                    name,
                    set_code,
                    set_name,
                    rarity,
                    mana_cost,
                    type_line,
                    image_small,
                    image_normal,
                    scryfall_uri,
                    finish,
                    quantity,
                    avg_price
                FROM grouped
                {where_sql}
                ORDER BY {order_sql}
                LIMIT :limit_value OFFSET :offset_value
                """
            )

            result = conn.execute(query, {
                **binds,
                "limit_value": length,
                "offset_value": start,
            }).mappings().all()

        return {
            "draw": draw,
            "recordsTotal": records_total,
            "recordsFiltered": records_filtered,
            "data": [dict(row) for row in result],
        }