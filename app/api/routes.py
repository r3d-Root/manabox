from flask.views import MethodView
from flask_smorest import Blueprint
from sqlalchemy import select, func

from app.extensions import db
from app.models.sync_status import SyncStatus
from app.services.importer import get_collection_table
from .schemas import HealthSchema, CollectionMetaSchema, SyncStatusSchema

api_bp = Blueprint("api", __name__, url_prefix="/api", description="ManaBox API")


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