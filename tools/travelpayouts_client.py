"""Travelpayouts (Aviasales) Data API client — free, token-based.

Primary source since Amadeus Self-Service was decommissioned (2026-07-17).
Prices are cached from real Aviasales user searches (last ~48h): great for
trend tracking and deal detection, but re-verify before booking.

Docs: https://support.travelpayouts.com/hc/en-us/articles/203956163
"""
import os

import requests

API = "https://api.travelpayouts.com"
TRIP_CLASS = {"ECONOMY": 0, "BUSINESS": 1}


def prices_for_dates(origin, destination, departure_at, return_at,
                     cabin="ECONOMY", currency="EUR", limit=100):
    """Cheapest cached round-trip tickets for a date or a whole month.

    departure_at / return_at accept 'YYYY-MM-DD' or 'YYYY-MM' (whole month).
    Returns a list of dicts:
    {depart_date, return_date, price_eur, airline, origin_airport,
     destination_airport, transfers, link}
    """
    resp = requests.get(
        f"{API}/aviasales/v3/prices_for_dates",
        headers={"X-Access-Token": os.environ["TRAVELPAYOUTS_TOKEN"]},
        params={
            "origin": origin,
            "destination": destination,
            "departure_at": departure_at,
            "return_at": return_at,
            "trip_class": TRIP_CLASS.get(cabin, 0),
            "currency": currency.lower(),
            "one_way": "false",
            "unique": "false",
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
            "return_date": (r.get("return_at") or "")[:10],
            "price_eur": float(r["price"]),
            "airline": r.get("airline"),
            "origin_airport": r.get("origin_airport"),
            "destination_airport": r.get("destination_airport"),
            "transfers": r.get("transfers"),
            "link": f"https://www.aviasales.com{link}" if link else None,
        })
    return out
