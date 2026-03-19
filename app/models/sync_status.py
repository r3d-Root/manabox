from datetime import datetime
from app.extensions import db


class SyncStatus(db.Model):
    __tablename__ = "sync_status"

    id = db.Column(db.Integer, primary_key=True)
    is_running = db.Column(db.Boolean, default=False, nullable=False)
    total_cards = db.Column(db.Integer, default=0, nullable=False)
    processed_cards = db.Column(db.Integer, default=0, nullable=False)
    current_scryfall_id = db.Column(db.String(64), nullable=True)
    current_card_name = db.Column(db.Text, nullable=True)
    last_error = db.Column(db.Text, nullable=True)
    started_at = db.Column(db.DateTime, nullable=True)
    finished_at = db.Column(db.DateTime, nullable=True)

    @staticmethod
    def get_singleton():
        status = SyncStatus.query.get(1)
        if not status:
            status = SyncStatus(id=1, started_at=datetime.utcnow())
            db.session.add(status)
            db.session.commit()
        return status