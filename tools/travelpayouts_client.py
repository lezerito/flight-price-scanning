"""Travelpayouts (Aviasales) Data API client — free, token-based.

Primary source since Amadeus Self-Service was decommissioned (2026-07-17).
Prices are cached from real Aviasales user searches (last ~48h): great for
trend tracking and deal detection, but re-verify before booking.

Hard constraints learned from the live API (2026-07-18):
- prices_for_dates rejects round trips with return > 30 days after departure
  → long stays must be tracked as two one-way legs.
- Economy only: trip_class is ignored by v3 and v2 rejects trip_class=1 with
  "Only economy trip class is supported". No business-class data exists here.

Docs: https://support.travelpayouts.com/hc/en-us/articles/203956163
"""
import os

import requests

API = "https://api.travelpayouts.com"


def one_way_prices(origin, destination, month, currency="EUR", limit=200):
    """Cheapest cached one-way tickets for a whole departure month.

    month: 'YYYY-MM'. Returns a list of dicts:
    {depart_date, price_eur, airline, origin_airport, destination_airport,
     transfers, link}
    """
    resp = requests.get(
        f"{API}/aviasales/v3/prices_for_dates",
        headers={"X-Access-Token": os.environ["TRAVELPAYOUTS_TOKEN"]},
        params={
            "origin": origin,
            "destination": destination,
            "departure_at": month,
            "one_way": "true",
            "unique": "false",
            "currency": currency.lower(),
            "sorting": "price",
            "limit": limit,
        },
        timeout=60,
    )
    resp.raise_for_status()
    rows = resp.json().get("data", [])
    out = []
    for r in rows:
        link = r.get("link")
        out.append({
            "depart_date": (r.get("departure_at") or "")[:10],
            "price_eur": float(r["price"]),
            "airline": r.get("airline"),
            "origin_airport": r.get("origin_airport"),
            "destination_airport": r.get("destination_airport"),
            "transfers": r.get("transfers"),
            "link": f"https://www.aviasales.com{link}" if link else None,
        })
    return out
