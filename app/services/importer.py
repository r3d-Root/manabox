import csv
import io
from sqlalchemy import Table, MetaData, select, inspect, text
from app.extensions import db
from app.models.collection import build_collection_table, normalize_column_name

def import_collection_csv(csv_bytes: bytes):
    decoded = csv_bytes.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(decoded))

    if not reader.fieldnames:
        raise ValueError("CSV file is missing a header row.")

    headers = reader.fieldnames
    table = build_collection_table(headers)

    with db.engine.begin() as conn:
        inspector = inspect(conn)
        if "collection_items" in inspector.get_table_names():
            conn.execute(text("DROP TABLE collection_items"))

        # rebuild cleanly
        db.metadata.clear()
        table = build_collection_table(headers)
        db.metadata.create_all(bind=conn, tables=[table])

        rows_to_insert = []
        for row in reader:
            cleaned = {}
            used_names = set()

            for original_key, value in row.items():
                col_name = normalize_column_name(original_key)

                if col_name in used_names:
                    suffix = 2
                    while f"{col_name}_{suffix}" in used_names:
                        suffix += 1
                    col_name = f"{col_name}_{suffix}"

                used_names.add(col_name)
                cleaned[col_name] = value

            rows_to_insert.append(cleaned)

        if rows_to_insert:
            conn.execute(table.insert(), rows_to_insert)

    return table

def get_collection_table():
    inspector = inspect(db.engine)
    if "collection_items" not in inspector.get_table_names():
        return None

    metadata = MetaData()
    return Table("collection_items", metadata, autoload_with=db.engine)

def fetch_all_rows(table):
    with db.engine.begin() as conn:
        return conn.execute(select(table)).fetchall()