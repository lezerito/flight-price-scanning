"""Build docs/index.html from the SQLite history (served via GitHub Pages)."""
import datetime as dt
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(__file__))
import db

ROOT = os.path.join(os.path.dirname(__file__), "..")
TEMPLATE = os.path.join(os.path.dirname(__file__), "dashboard_template.html")
OUT = os.path.join(ROOT, "docs", "index.html")
CONFIG_PATH = os.path.join(ROOT, "config.json")

SHORT = {("NYC", "TYO"): "→ TYO", ("NYC", "OSA"): "→ OSA",
         ("TYO", "NYC"): "TYO →", ("OSA", "NYC"): "OSA →",
         ("PAR", "NYC"): "PAR → NYC"}


def build_data(conn, cfg):
    meta = conn.execute(
        """SELECT COUNT(*) n, MIN(observed_at) first, MAX(observed_at) last
           FROM observations""").fetchone()
    last_day = meta["last"] or dt.date.today().isoformat()
    window_start = (dt.date.fromisoformat(last_day) - dt.timedelta(
        days=cfg["deal_rules"]["history_window_days"])).isoformat()

    watches, series = [], []
    for w in cfg["watches"]:
        key = (w["origin"], w["destination"], w["cabin"])
        best = conn.execute(
            """SELECT * FROM observations
               WHERE origin=? AND destination=? AND cabin=?
                 AND observed_at=?
               ORDER BY price_eur ASC LIMIT 1""", (*key, last_day)).fetchone()
        daily = conn.execute(
            """SELECT observed_at d, MIN(price_eur) p FROM observations
               WHERE origin=? AND destination=? AND cabin=?
                 AND observed_at >= ?
               GROUP BY observed_at ORDER BY observed_at""",
            (*key, window_start)).fetchall()
        history = [r["p"] for r in daily if r["d"] != last_day]
        median = round(statistics.median(history), 2) if len(history) >= \
            cfg["deal_rules"]["min_history_days"] else None

        # cheapest per departure day, latest scan (the month calendar)
        cal = conn.execute(
            """SELECT depart_date, MIN(price_eur) p, airline FROM observations
               WHERE origin=? AND destination=? AND cabin=?
                 AND observed_at=?
               GROUP BY depart_date ORDER BY depart_date""",
            (*key, last_day)).fetchall()
        watches.append({
            "name": w["name"], "origin": w["origin"],
            "destination": w["destination"],
            "months": w.get("months") or [w["month"]],
            "median": median,
            "best": {"price": best["price_eur"], "depart": best["depart_date"],
                     "airline": best["airline"],
                     "airports": (f"{best['origin_airport']}→"
                                  f"{best['destination_airport']}"
                                  if best["origin_airport"] else None),
                     "link": best["deep_link"]} if best else None,
            "calendar": [{"date": c["depart_date"], "price": c["p"],
                          "airline": c["airline"]} for c in cal],
        })
        series.append({
            "label": w["name"],
            "short": SHORT.get((w["origin"], w["destination"]), w["destination"]),
            "panel": w["panel"], "color_slot": len(series) % 4,
            "points": [{"date": r["d"], "price": r["p"]} for r in daily],
        })

    by_name = {w["name"]: w for w in watches}
    trips = []
    for pair in cfg.get("trip_pairs", []):
        o, r = by_name.get(pair["out"]), by_name.get(pair["ret"])
        if o and o["best"] and r and r["best"]:
            trips.append({
                "city": pair["city"],
                "total": round(o["best"]["price"] + r["best"]["price"], 2),
                "out_price": o["best"]["price"], "ret_price": r["best"]["price"],
                "out_date": o["best"]["depart"], "ret_date": r["best"]["depart"],
            })

    deals = conn.execute(
        """SELECT d.detected_at, d.pct_below_median, o.origin, o.destination,
                  o.cabin, o.depart_date, o.return_date, o.price_eur, o.deep_link
           FROM deals d JOIN observations o ON o.id = d.observation_id
           ORDER BY d.detected_at DESC, o.price_eur ASC LIMIT 15""").fetchall()

    return {
        "generated_at": last_day,
        "n_observations": meta["n"],
        "first_observation": meta["first"] or "—",
        "watches": watches,
        "series": series,
        "trips": trips,
        "deals": [dict(d) for d in deals],
    }


def main():
    with open(CONFIG_PATH) as f:
        cfg = json.load(f)
    conn = db.connect()
    data = build_data(conn, cfg)
    conn.close()
    with open(TEMPLATE) as f:
        html = f.read()
    html = html.replace("/*__DATA__*/null", json.dumps(data))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        f.write(html)
    print(f"dashboard written: {os.path.abspath(OUT)} "
          f"({data['n_observations']} observations)")


if __name__ == "__main__":
    main()
