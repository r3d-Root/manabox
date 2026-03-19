from datetime import datetime
from app.extensions import db


class ScryfallCard(db.Model):
    __tablename__ = "scryfall_cards"

    scryfall_id = db.Column(db.String(64), primary_key=True)
    name = db.Column(db.Text, nullable=True)
    set_code = db.Column(db.Text, nullable=True)
    set_name = db.Column(db.Text, nullable=True)
    collector_number = db.Column(db.Text, nullable=True)
    rarity = db.Column(db.Text, nullable=True)
    mana_cost = db.Column(db.Text, nullable=True)
    type_line = db.Column(db.Text, nullable=True)
    oracle_text = db.Column(db.Text, nullable=True)
    image_small = db.Column(db.Text, nullable=True)
    image_normal = db.Column(db.Text, nullable=True)
    scryfall_uri = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)