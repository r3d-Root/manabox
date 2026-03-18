from flask.views import MethodView
from flask_smorest import Blueprint
from sqlalchemy import select, func

from app.extensions import db
from app.services.importer import get_collection_table
from .schemas import HealthSchema, CollectionMetaSchema

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