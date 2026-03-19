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


class UpdatedCardSchema(Schema):
    scryfall_id = fields.String(required=True)
    name = fields.String(allow_none=True)
    set_code = fields.String(allow_none=True)
    set_name = fields.String(allow_none=True)
    collector_number = fields.String(allow_none=True)
    rarity = fields.String(allow_none=True)
    mana_cost = fields.String(allow_none=True)
    type_line = fields.String(allow_none=True)
    image_small = fields.String(allow_none=True)
    image_normal = fields.String(allow_none=True)
    scryfall_uri = fields.String(allow_none=True)
    updated_at = fields.String(required=True)


class UpdatedCardsResponseSchema(Schema):
    cards = fields.List(fields.Nested(UpdatedCardSchema), required=True)