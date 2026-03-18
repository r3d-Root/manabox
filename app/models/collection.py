from sqlalchemy import Table, Column, Integer, Text
from app.extensions import db

def normalize_column_name(name: str) -> str:
    value = name.strip().lower()
    value = value.replace(" ", "_").replace("-", "_").replace("/", "_")
    value = "".join(ch for ch in value if ch.isalnum() or ch == "_")
    if not value:
        value = "column"
    if value[0].isdigit():
        value = f"col_{value}"
    return value

def build_collection_table(column_names):
    columns = [Column("id", Integer, primary_key=True, autoincrement=True)]
    seen = {"id"}

    for original_name in column_names:
        col_name = normalize_column_name(original_name)

        if col_name in seen:
            suffix = 2
            while f"{col_name}_{suffix}" in seen:
                suffix += 1
            col_name = f"{col_name}_{suffix}"

        seen.add(col_name)
        columns.append(Column(col_name, Text, nullable=True))

    return Table("collection_items", db.metadata, *columns, extend_existing=True)