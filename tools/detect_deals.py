"""Deal detection: compare today's best prices against the recent price
history for the same route+cabin (rolling window, current month to start).

A deal fires when today's best price is below the configured percentile of
daily best prices, or more than X% below the rolling median (X is higher for
business class, to catch only big drops). With fewer than min_history_days of
history, no alert fires (cold start — we're still collecting).
"""
import datetime as dt
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(__file__))
import db

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config.json")


def percentile(sorted_vals, pct):
    if not sorted_vals:
        return None
    k = (len(sorted_vals) - 1) * pct / 100
    lo, hi = int(k), min(int(k) + 1, len(sorted_vals) - 1)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (k - lo)


def detect(conn, cfg, today):
    rules = cfg["deal_rules"]
    window_start = (dt.date.fromisoformat(today)
                    - dt.timedelta(days=rules["history_window_days"])).isoformat()
    deals = []
    routes = conn.execute(
        """SELECT DISTINCT origin, destination, cabin FROM observations
           WHERE source != 'travelpayouts'""").fetchall()
    for r in routes:
        # Daily best price for this route+cabin over the window (excl. today).
        history = [row["p"] for row in conn.execute(
            """SELECT observed_at, MIN(price_eur) p FROM observations
               WHERE origin=? AND destination=? AND cabin=?
                 AND source != 'travelpayouts'
                 AND observed_at >= ? AND observed_at < ?
               GROUP BY observed_at ORDER BY observed_at""",
            (r["origin"], r["destination"], r["cabin"], window_start, today))]
        if len(history) < rules["min_history_days"]:
            continue
        best_today = conn.execute(
            """SELECT * FROM observations
               WHERE origin=? AND destination=? AND cabin=?
                 AND source != 'travelpayouts' AND observed_at=?
               ORDER BY price_eur ASC LIMIT 1""",
            (r["origin"], r["destination"], r["cabin"], today)).fetchone()
        if not best_today:
            continue
        median = statistics.median(history)
        p_trigger = percentile(sorted(history), rules["percentile_trigger"])
        drop_pct_needed = (rules["business_drop_pct"] if r["cabin"] == "BUSINESS"
                           else rules["economy_drop_pct"])
        pct_below = (median - best_today["price_eur"]) / median * 100
        reasons = []
        if best_today["price_eur"] <= p_trigger:
            reasons.append(f"below {rules['percentile_trigger']}th percentile "
                           f"of last {len(history)} days")
        if pct_below >= drop_pct_needed:
            reasons.append(f"{pct_below:.0f}% below {len(history)}-day median")
        if not reasons:
            continue
        # Don't re-alert the same route+cabin at the same or higher price
        # within the last 3 days.
        recent = conn.execute(
            """SELECT MIN(o.price_eur) p FROM deals d
               JOIN observations o ON o.id = d.observation_id
               WHERE o.origin=? AND o.destination=? AND o.cabin=?
                 AND d.detected_at >= ?""",
            (r["origin"], r["destination"], r["cabin"],
             (dt.date.fromisoformat(today) - dt.timedelta(days=3)).isoformat())
        ).fetchone()["p"]
        if recent is not None and best_today["price_eur"] >= recent * 0.99:
            continue
        conn.execute(
            """INSERT INTO deals (detected_at, observation_id, reason,
                                  baseline_median, pct_below_median)
               VALUES (?,?,?,?,?)""",
            (today, best_today["id"], "; ".join(reasons), median,
             round(pct_below, 1)))
        deals.append({
            "origin": best_today["origin"],
            "destination": best_today["destination"],
            "origin_airport": best_today["origin_airport"],
            "destination_airport": best_today["destination_airport"],
            "cabin": best_today["cabin"],
            "depart_date": best_today["depart_date"],
            "return_date": best_today["return_date"],
            "price_eur": best_today["price_eur"],
            "airline": best_today["airline"],
            "deep_link": best_today["deep_link"],
            "baseline_median": round(median, 2),
            "pct_below_median": round(pct_below, 1),
            "reason": "; ".join(reasons),
        })
    return deals


def main():
    with open(CONFIG_PATH) as f:
        cfg = json.load(f)
    today = dt.date.today().isoformat()
    conn = db.connect()
    with conn:
        deals = detect(conn, cfg, today)
    conn.close()
    print(json.dumps(deals, indent=2))
    return deals


if __name__ == "__main__":
    main()
