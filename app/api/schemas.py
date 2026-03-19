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


class FilterOptionsSchema(Schema):
    sets = fields.List(fields.String(), required=True)
    rarities = fields.List(fields.String(), required=True)
    finishes = fields.List(fields.String(), required=True)


class TableRowSchema(Schema):
    scryfall_id = fields.String(allow_none=True)
    name = fields.String(allow_none=True)
    set_code = fields.String(allow_none=True)
    set_name = fields.String(allow_none=True)
    rarity = fields.String(allow_none=True)
    mana_cost = fields.String(allow_none=True)
    type_line = fields.String(allow_none=True)
    image_small = fields.String(allow_none=True)
    image_normal = fields.String(allow_none=True)
    scryfall_uri = fields.String(allow_none=True)
    finish = fields.String(allow_none=True)
    quantity = fields.Integer(allow_none=True)
    avg_price = fields.String(allow_none=True)


class TableDataResponseSchema(Schema):
    draw = fields.Integer(required=True)
    recordsTotal = fields.Integer(required=True)
    recordsFiltered = fields.Integer(required=True)
    data = fields.List(fields.Nested(TableRowSchema), required=True)


class TableDataQuerySchema(Schema):
    draw = fields.Integer(load_default=1)
    start = fields.Integer(load_default=0)
    length = fields.Integer(load_default=50)

    search_value = fields.String(load_default="", data_key="search[value]")
    order_column = fields.String(load_default="1", data_key="order[0][column]")
    order_dir = fields.String(load_default="asc", data_key="order[0][dir]")

    set_filter = fields.String(load_default="")
    rarity_filter = fields.String(load_default="")
    finish_filter = fields.String(load_default="")