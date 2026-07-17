"""Daily orchestrator: scan -> detect deals -> email -> rebuild dashboard.

This is what GitHub Actions runs. Each step is fault-isolated: a mail failure
never loses scan data.
"""
import datetime as dt
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import db
import detect_deals
import scan
import send_alert


def main():
    cfg = scan.load_config()
    today = dt.date.today().isoformat()
    mock = os.environ.get("MOCK_SCAN") == "1" or "--mock" in sys.argv

    conn = db.connect()
    with conn:
        if mock:
            print(f"[1/4] mock scan: {scan.scan_mock(conn, cfg, today)} observations")
        else:
            print(f"[1/4] amadeus scan: {scan.scan_amadeus(conn, cfg, today)} observations")
            if os.environ.get("TRAVELPAYOUTS_TOKEN"):
                print(f"      travelpayouts: {scan.scan_travelpayouts(conn, cfg, today)} observations")
            else:
                print("      travelpayouts: skipped (no token)")

    with conn:
        deals = detect_deals.detect(conn, cfg, today)
    conn.close()
    print(f"[2/4] deals detected: {len(deals)}")
    if deals:
        print(json.dumps(deals, indent=2))

    try:
        send_alert.send(deals)
        print("[3/4] alerts done")
    except Exception as e:
        print(f"[3/4] alert failed (non-fatal): {e}")

    import build_dashboard
    build_dashboard.main()
    print("[4/4] dashboard rebuilt")


if __name__ == "__main__":
    main()
