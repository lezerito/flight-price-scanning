"""Minimal Amadeus Self-Service API client (free tier).

Test env returns cached/limited data but works for major routes like NYC-TYO.
Switch to production with AMADEUS_ENV=production once ready (also free tier).
"""
import os
import time

import requests

BASE_URLS = {
    "test": "https://test.api.amadeus.com",
    "production": "https://api.amadeus.com",
}

_token = {"value": None, "expires_at": 0}


def _base_url():
    return BASE_URLS[os.environ.get("AMADEUS_ENV", "test")]


def _get_token():
    if _token["value"] and time.time() < _token["expires_at"] - 60:
        return _token["value"]
    resp = requests.post(
        f"{_base_url()}/v1/security/oauth2/token",
        data={
            "grant_type": "client_credentials",
            "client_id": os.environ["AMADEUS_CLIENT_ID"],
            "client_secret": os.environ["AMADEUS_CLIENT_SECRET"],
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    _token["value"] = data["access_token"]
    _token["expires_at"] = time.time() + data.get("expires_in", 1799)
    return _token["value"]


def search_cheapest(origin, destination, depart_date, return_date, cabin="ECONOMY",
                    currency="EUR", max_offers=3):
    """Return the cheapest offer dict for one date pair, or None if no offers.

    Result: {price_eur, airline, origin_airport, destination_airport}
    """
    resp = requests.get(
        f"{_base_url()}/v2/shopping/flight-offers",
        headers={"Authorization": f"Bearer {_get_token()}"},
        params={
            "originLocationCode": origin,
            "destinationLocationCode": destination,
            "departureDate": depart_date,
            "returnDate": return_date,
            "adults": 1,
            "travelClass": cabin,
            "currencyCode": currency,
            "max": max_offers,
        },
        timeout=60,
    )
    if resp.status_code == 429:
        # Rate limited: back off once, then retry.
        time.sleep(3)
        return search_cheapest(origin, destination, depart_date, return_date,
                               cabin, currency, max_offers)
    resp.raise_for_status()
    offers = resp.json().get("data", [])
    if not offers:
        return None
    best = min(offers, key=lambda o: float(o["price"]["grandTotal"]))
    out_segments = best["itineraries"][0]["segments"]
    return {
        "price_eur": float(best["price"]["grandTotal"]),
        "airline": (best.get("validatingAirlineCodes") or [None])[0],
        "origin_airport": out_segments[0]["departure"]["iataCode"],
        "destination_airport": out_segments[-1]["arrival"]["iataCode"],
    }
