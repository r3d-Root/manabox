import requests
from app.extensions import db
from app.models.scryfall import ScryfallCard

SCRYFALL_API = "https://api.scryfall.com/cards"


def fetch_card_by_id(scryfall_id: str) -> dict:
    response = requests.get(f"{SCRYFALL_API}/{scryfall_id}", timeout=30)
    response.raise_for_status()
    return response.json()


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


def upsert_scryfall_card(scryfall_id: str):
    if not scryfall_id:
        return None

    existing = db.session.get(ScryfallCard, scryfall_id)
    if existing:
        return existing

    card_json = fetch_card_by_id(scryfall_id)
    image_small, image_normal = extract_images(card_json)

    card = ScryfallCard(
        scryfall_id=scryfall_id,
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
    )

    db.session.add(card)
    db.session.flush()
    return card