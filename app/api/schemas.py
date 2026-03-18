from marshmallow import Schema, fields

class HealthSchema(Schema):
    status = fields.String(required=True)

class CollectionMetaSchema(Schema):
    row_count = fields.Integer(required=True)
    columns = fields.List(fields.String(), required=True)