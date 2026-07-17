"""Travelpayouts (Aviasales) Data API client — free cached prices.

Caveat: cached prices reflect typical trip durations searched by other users,
not a 6-month stay. Useful as a broad signal for cheap departure days and
overall price level, not as a bookable quote for our exact trip.
"""
import os

import requests

API = "https://api.travelpayouts.com"


def month_matrix(origin, destination, month, currency="EUR"):
    """Cheapest cached price per departure day for one month.

    month: 'YYYY-MM-01'. Returns list of dicts:
    {depart_date, return_date, price_eur, airline(None), ...}
    """
    resp = requests.get(
        f"{API}/v2/prices/month-matrix",
        headers={"X-Access-Token": os.environ["TRAVELPAYOUTS_TOKEN"]},
        params={
            "currency": currency.lower(),
            "origin": origin,
            "destination": destination,
            "month": month,
            "show_to_affiliates": "false",
        },
        timeout=60,
    )
    resp.raise_for_status()
    rows = resp.json().get("data", [])
    out = []
    for r in rows:
        out.append({
            "depart_date": r.get("depart_date"),
            "return_date": r.get("return_date"),
            "price_eur": float(r.get("value")),
            "airline": r.get("gate"),
        })
    return out
