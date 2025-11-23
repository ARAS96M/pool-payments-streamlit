import json
from sqlalchemy.orm import Session
from models import Club, Pricing

DAYS = ["samedi","dimanche","lundi","mardi","mercredi","jeudi"]

def get_price(session: Session, key: str, default=0.0):
    p = session.query(Pricing).filter_by(key=key).first()
    return p.value if p else default

def compute_club_total(session: Session, days_config_json: str, frais_key="frais_prestation"):
    cfg = json.loads(days_config_json)
    pb_price = get_price(session, "PB_price", 1200)
    lane_price = get_price(session, "lane_price", 1200)
    total = 0.0
    for day in cfg:
        item = cfg[day]
        # item exemple: {"type":"PB", "nb_lane": 2}
        if item.get("type") == "PB":
            total += pb_price * 1  # PB = one unit per day
        # si couloir (lane)
        if item.get("nb_lane"):
            total += lane_price * int(item["nb_lane"])
    # ajouter frais prestation (une fois)
    frais = get_price(session, frais_key, 0)
    total += frais
    return total
