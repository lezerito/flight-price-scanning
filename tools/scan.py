"""Daily scan: one Travelpayouts v3 one-way query per watched leg (whole
departure month), recording every cached fare in SQLite.

The trip is tracked as two one-way legs (out Sep 2026, back Mar 2027) because
the API rejects round trips with a >30-day spread — and a 6-month stay is
usually booked as two one-ways anyway.

MOCK_SCAN=1 (or --mock) generates plausible data with no API calls, including
a 30-day backfill on an empty DB so the full pipeline can be tested.
"""
import datetime as dt
import hashlib
import json
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
import db

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config.json")


def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)


def date_grid(window):
    start = dt.date.fromisoformat(window["start"])
    end = dt.date.fromisoformat(window["end"])
    step = dt.timedelta(days=window["step_days"])
    dates, d = [], start
    while d <= end:
        dates.append(d.isoformat())
        d += step
    return dates


def google_flights_link(origin, destination, depart):
    return (f"https://www.google.com/travel/flights?q=Flights%20from%20{origin}"
            f"%20to%20{destination}%20on%20{depart}%20one%20way")


# ---------------------------------------------------------------- real scan

def scan_travelpayouts(conn, cfg, today):
    import travelpayouts_client
    n = 0
    for watch in cfg["watches"]:
        rows = []
        for month in watch.get("months") or [watch["month"]]:
            try:
                rows += travelpayouts_client.one_way_prices(
                    watch["origin"], watch["destination"], month,
                    currency=cfg["currency"])
            except Exception as e:  # keep scanning other watches/months
                print(f"  travelpayouts error {watch['name']} {month}: {e}")
        for r in rows:
            if not r["depart_date"]:
                continue
            # API only takes whole months; enforce day-level window here.
            if watch.get("depart_from") and r["depart_date"] < watch["depart_from"]:
                continue
            if watch.get("depart_to") and r["depart_date"] > watch["depart_to"]:
                continue
            db.insert_observation(conn, {
                "observed_at": today, "source": "travelpayouts",
                "origin": watch["origin"], "destination": watch["destination"],
                "origin_airport": r["origin_airport"],
                "destination_airport": r["destination_airport"],
                "depart_date": r["depart_date"], "return_date": None,
                "cabin": watch["cabin"], "price_eur": r["price_eur"],
                "airline": r["airline"],
                "deep_link": r["link"] or google_flights_link(
                    watch["origin"], watch["destination"], r["depart_date"]),
            })
            n += 1
        time.sleep(0.3)
    return n


# ---------------------------------------------------------------- mock scan

MOCK_BASE = {("NYC", "TYO"): 450, ("NYC", "OSA"): 480,
             ("TYO", "NYC"): 420, ("OSA", "NYC"): 460}


def _mock_price(origin, destination, depart, day):
    seed = int(hashlib.md5(f"{origin}{destination}{depart}{day}".encode())
               .hexdigest()[:8], 16)
    rng = random.Random(seed)
    base = MOCK_BASE[(origin, destination)]
    price = base * rng.uniform(0.85, 1.20)
    if rng.random() < 0.04:  # occasional genuine dip
        price *= 0.70
    return round(price, 2)


def scan_mock(conn, cfg, today):
    today_d = dt.date.fromisoformat(today)
    empty = conn.execute("SELECT COUNT(*) c FROM observations").fetchone()["c"] == 0
    days = [today_d - dt.timedelta(days=i) for i in range(29, -1, -1)] if empty \
        else [today_d]
    n = 0
    for day in days:
        day_s = day.isoformat()
        for watch in cfg["watches"]:
            for depart in date_grid(watch["mock_window"]):
                db.insert_observation(conn, {
                    "observed_at": day_s, "source": "mock",
                    "origin": watch["origin"], "destination": watch["destination"],
                    "origin_airport": "EWR" if watch["origin"] == "NYC" else "NRT",
                    "destination_airport": "NRT" if watch["origin"] == "NYC" else "EWR",
                    "depart_date": depart, "return_date": None,
                    "cabin": watch["cabin"],
                    "price_eur": _mock_price(watch["origin"], watch["destination"],
                                             depart, day_s),
                    "airline": "NH",
                    "deep_link": google_flights_link(
                        watch["origin"], watch["destination"], depart),
                })
                n += 1
    return n


def main():
    cfg = load_config()
    today = dt.date.today().isoformat()
    mock = os.environ.get("MOCK_SCAN") == "1" or "--mock" in sys.argv
    conn = db.connect()
    with conn:
        if mock:
            n = scan_mock(conn, cfg, today)
            print(f"mock scan: {n} observations")
        else:
            n = scan_travelpayouts(conn, cfg, today)
            print(f"travelpayouts: {n} observations")
    conn.close()


if __name__ == "__main__":
    main()
