from marshmallow import Schema, fields


class HealthSchema(Schema):
    status = fields.String(required=True)


class CollectionMetaSchema(Schema):
    row_count = fields.Integer(required=True)
    columns = fields.List(fields.String(), required=True)


class SyncStatusSchema(Schema):
    is_running = fields.Boolean(required=True)
    total_cards = fields.Integer(required=True)
    processed_cards = fields.Integer(required=True)
    current_scryfall_id = fields.String(allow_none=True)
    current_card_name = fields.String(allow_none=True)
    last_error = fields.String(allow_none=True)
    percent = fields.Float(required=True)