"""Daily scan: query the Travelpayouts/Aviasales v3 API for each watched
route+cabin over whole departure/return months, and record every price
observation in SQLite.

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


def google_flights_link(origin, destination, depart, ret, cabin):
    cabin_txt = "%20business%20class" if cabin == "BUSINESS" else ""
    return (f"https://www.google.com/travel/flights?q=Flights%20from%20{origin}"
            f"%20to%20{destination}%20on%20{depart}%20through%20{ret}{cabin_txt}")


# ---------------------------------------------------------------- real scan

def scan_travelpayouts(conn, cfg, today):
    """One month-pair query per watch: every cached ticket found in the last
    ~48h for depart-month x return-month becomes an observation."""
    import travelpayouts_client
    n = 0
    for watch in cfg["watches"]:
        try:
            rows = travelpayouts_client.prices_for_dates(
                watch["origin"], watch["destination"],
                watch["depart_month"], watch["return_month"],
                cabin=watch["cabin"], currency=cfg["currency"])
        except Exception as e:  # keep scanning other watches
            print(f"  travelpayouts error {watch['name']}: {e}")
            continue
        for r in rows:
            if not r["depart_date"]:
                continue
            db.insert_observation(conn, {
                "observed_at": today, "source": "travelpayouts",
                "origin": watch["origin"], "destination": watch["destination"],
                "origin_airport": r["origin_airport"],
                "destination_airport": r["destination_airport"],
                "depart_date": r["depart_date"], "return_date": r["return_date"],
                "cabin": watch["cabin"], "price_eur": r["price_eur"],
                "airline": r["airline"],
                "deep_link": r["link"] or google_flights_link(
                    watch["origin"], watch["destination"], r["depart_date"],
                    r["return_date"], watch["cabin"]),
            })
            n += 1
        time.sleep(0.3)
    return n


# ---------------------------------------------------------------- mock scan

MOCK_BASE = {("TYO", "ECONOMY"): 950, ("OSA", "ECONOMY"): 1010,
             ("TYO", "BUSINESS"): 3800, ("OSA", "BUSINESS"): 4100}


def _mock_price(destination, cabin, depart, ret, day):
    seed = int(hashlib.md5(f"{destination}{cabin}{depart}{ret}{day}".encode())
               .hexdigest()[:8], 16)
    rng = random.Random(seed)
    base = MOCK_BASE[(destination, cabin)]
    price = base * rng.uniform(0.88, 1.18)
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
            for depart in date_grid(watch["mock_depart_window"]):
                for ret in date_grid(watch["mock_return_window"]):
                    db.insert_observation(conn, {
                        "observed_at": day_s, "source": "mock",
                        "origin": watch["origin"], "destination": watch["destination"],
                        "origin_airport": "EWR", "destination_airport": "NRT",
                        "depart_date": depart, "return_date": ret,
                        "cabin": watch["cabin"],
                        "price_eur": _mock_price(watch["destination"], watch["cabin"],
                                                 depart, ret, day_s),
                        "airline": "NH",
                        "deep_link": google_flights_link(
                            watch["origin"], watch["destination"], depart, ret,
                            watch["cabin"]),
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
