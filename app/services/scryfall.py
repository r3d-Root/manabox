from datetime import datetime
import time
import requests

from app.extensions import db
from app.models.scryfall import ScryfallCard

SCRYFALL_COLLECTION_API = "https://api.scryfall.com/cards/collection"
BATCH_SIZE = 75
BATCH_DELAY_SECONDS = 0.12
MAX_RETRIES = 4


def extract_images(card_json: dict):
    image_small = None
    image_normal = None

    if card_json.get("image_uris"):
        image_small = card_json["image_uris"].get("small")
        image_normal = card_json["image_uris"].get("normal")
    elif card_json.get("card_faces"):
        first_face = card_json["card_faces"][0]
        if first_face.get("image_uris"):
            image_small = first_face["image_uris"].get("small")
            image_normal = first_face["image_uris"].get("normal")

    return image_small, image_normal


def chunked(values, size):
    for i in range(0, len(values), size):
        yield values[i:i + size]


def build_card_model(card_json: dict):
    image_small, image_normal = extract_images(card_json)
    prices = card_json.get("prices") or {}

    return ScryfallCard(
        scryfall_id=card_json.get("id"),
        name=card_json.get("name"),
        set_code=card_json.get("set"),
        set_name=card_json.get("set_name"),
        collector_number=card_json.get("collector_number"),
        rarity=card_json.get("rarity"),
        mana_cost=card_json.get("mana_cost"),
        type_line=card_json.get("type_line"),
        oracle_text=card_json.get("oracle_text"),
        image_small=image_small,
        image_normal=image_normal,
        scryfall_uri=card_json.get("scryfall_uri"),
        usd=prices.get("usd"),
        usd_foil=prices.get("usd_foil"),
        updated_at=datetime.utcnow(),
    )


def fetch_cards_collection_batch(scryfall_ids):
    identifiers = [{"id": scryfall_id} for scryfall_id in scryfall_ids]

    last_response = None

    for attempt in range(MAX_RETRIES):
        response = requests.post(
            SCRYFALL_COLLECTION_API,
            json={"identifiers": identifiers},
            timeout=60,
        )
        last_response = response

        if response.status_code == 429:
            sleep_seconds = min(2 ** attempt, 8)
            time.sleep(sleep_seconds)
            continue

        response.raise_for_status()
        return response.json()

    if last_response is not None:
        last_response.raise_for_status()

    raise RuntimeError("Scryfall batch request failed without a response.")


def upsert_scryfall_cards_batch(scryfall_ids):
    if not scryfall_ids:
        return {
            "saved_ids": [],
            "not_found_ids": [],
            "warnings": [],
        }

    payload = fetch_cards_collection_batch(scryfall_ids)

    saved_ids = []
    not_found_ids = []
    warnings = []

    for card_json in payload.get("data", []):
        scryfall_id = card_json.get("id")
        if not scryfall_id:
            continue

        prices = card_json.get("prices") or {}
        image_small, image_normal = extract_images(card_json)

        existing = db.session.get(ScryfallCard, scryfall_id)
        if existing:
            existing.name = card_json.get("name")
            existing.set_code = card_json.get("set")
            existing.set_name = card_json.get("set_name")
            existing.collector_number = card_json.get("collector_number")
            existing.rarity = card_json.get("rarity")
            existing.mana_cost = card_json.get("mana_cost")
            existing.type_line = card_json.get("type_line")
            existing.oracle_text = card_json.get("oracle_text")
            existing.image_small = image_small
            existing.image_normal = image_normal
            existing.scryfall_uri = card_json.get("scryfall_uri")
            existing.usd = prices.get("usd")
            existing.usd_foil = prices.get("usd_foil")
            existing.updated_at = datetime.utcnow()
        else:
            db.session.add(build_card_model(card_json))

        saved_ids.append(scryfall_id)

    for warning in payload.get("warnings", []):
        warnings.append(str(warning))

    found_set = set(saved_ids)
    for requested_id in scryfall_ids:
        if requested_id not in found_set:
            not_found_ids.append(requested_id)

    return {
        "saved_ids": saved_ids,
        "not_found_ids": not_found_ids,
        "warnings": warnings,
    }


def sync_batch_with_delay(scryfall_ids):
    results = {
        "saved_ids": [],
        "not_found_ids": [],
        "warnings": [],
    }

    for batch in chunked(scryfall_ids, BATCH_SIZE):
        batch_result = upsert_scryfall_cards_batch(batch)
        results["saved_ids"].extend(batch_result["saved_ids"])
        results["not_found_ids"].extend(batch_result["not_found_ids"])
        results["warnings"].extend(batch_result["warnings"])

        db.session.commit()
        time.sleep(BATCH_DELAY_SECONDS)

    return results