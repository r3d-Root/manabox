import csv
import io
import threading
from datetime import datetime
from sqlalchemy import Table, MetaData, select, inspect, text

from app.extensions import db
from app.models.collection import build_collection_table, normalize_column_name
from app.models.sync_status import SyncStatus
from app.services.scryfall import upsert_scryfall_card


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

        if "scryfall_cards" not in inspector.get_table_names():
            db.metadata.create_all(bind=conn)

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

        table.create(bind=conn, checkfirst=True)

        if rows_to_insert:
            conn.execute(table.insert(), rows_to_insert)

    return table


def get_missing_scryfall_ids():
    query = text("""
        SELECT DISTINCT c.scryfall_id
        FROM collection_items c
        LEFT JOIN scryfall_cards s
            ON c.scryfall_id = s.scryfall_id
        WHERE c.scryfall_id IS NOT NULL
          AND TRIM(c.scryfall_id) != ''
          AND s.scryfall_id IS NULL
        ORDER BY c.scryfall_id
    """)

    with db.engine.begin() as conn:
        rows = conn.execute(query).fetchall()

    return [row[0] for row in rows]


def sync_scryfall_cards_with_progress(app):
    with app.app_context():
        status = SyncStatus.get_singleton()

        if status.is_running:
            return

        missing_ids = get_missing_scryfall_ids()

        status.is_running = True
        status.total_cards = len(missing_ids)
        status.processed_cards = 0
        status.current_scryfall_id = None
        status.current_card_name = None
        status.last_error = None
        status.started_at = datetime.utcnow()
        status.finished_at = None
        db.session.commit()

        try:
            for idx, scryfall_id in enumerate(missing_ids, start=1):
                status.current_scryfall_id = scryfall_id
                status.current_card_name = None
                db.session.commit()

                try:
                    card = upsert_scryfall_card(scryfall_id)
                    if card:
                        status.current_card_name = card.name
                    db.session.commit()
                except Exception as exc:
                    db.session.rollback()
                    status.last_error = f"{scryfall_id}: {exc}"
                    db.session.commit()

                status.processed_cards = idx
                db.session.commit()
        finally:
            status.is_running = False
            status.current_scryfall_id = None
            status.finished_at = datetime.utcnow()
            db.session.commit()


def start_scryfall_sync_background(app):
    with app.app_context():
        status = SyncStatus.get_singleton()
        if status.is_running:
            return

    thread = threading.Thread(
        target=sync_scryfall_cards_with_progress,
        args=(app,),
        daemon=True,
    )
    thread.start()


def get_collection_table():
    inspector = inspect(db.engine)
    if "collection_items" not in inspector.get_table_names():
        return None

    metadata = MetaData()
    return Table("collection_items", metadata, autoload_with=db.engine)


def fetch_all_rows(table):
    with db.engine.begin() as conn:
        return conn.execute(select(table)).fetchall()