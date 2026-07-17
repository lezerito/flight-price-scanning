# Workflow: Flight Price Scan (NYC ⇄ Japan)

## Objective
Collect flight prices daily for EWR/JFK ⇄ Japan as **four one-way legs**
(NYC→TYO and NYC→OSA in Sep 2026; TYO→NYC and OSA→NYC in Mar 2027), build a
price history, detect deals, email alerts in EUR with booking links, and
publish an HTML dashboard with round-trip totals (out + back).

## Inputs
- `config.json` — watched routes (origin/destination/cabin + depart/return
  months), deal thresholds.
- Secrets in `.env` locally, GitHub Actions Secrets in the cloud:
  `TRAVELPAYOUTS_TOKEN`, `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD`, `MAIL_TO`.

## Tools (run in this order — or just `tools/run_daily.py` which chains them)
1. `tools/scan.py` — one Travelpayouts v3 `prices_for_dates` query per leg
   (`one_way=true`, whole departure month) → appends every cached fare to
   `data/prices.sqlite`.
2. `tools/detect_deals.py` — compares today's best vs rolling 30-day history.
3. `tools/send_alert.py` — Gmail SMTP alert; prints instead of sending when
   mail secrets are absent.
4. `tools/build_dashboard.py` — regenerates `docs/index.html`.

## Scheduling
`.github/workflows/daily-scan.yml` runs everything daily at 06:00 UTC and
commits `data/` + `docs/` back to the repo. This is how the system keeps
collecting/learning with no machine of ours running.

## Design decisions & constraints (learned)
- **2026-07-17: Amadeus Self-Service portal decommissioned** (keys dead, new
  registrations closed since spring 2026). Travelpayouts/Aviasales v3
  `prices_for_dates` is now the primary source: free, month-granularity
  `departure_at` (YYYY-MM), EUR support, aviasales booking links. Enterprise
  Amadeus is contract-only — not an option for a free system.
- **One-way legs, not round trips (2026-07-18, verified live)**: the API
  rejects round trips with return >30 days after departure ("diff between max
  depart date and min return date exceeds supported maximum of 30"). The
  Sep→Mar trip is therefore tracked as two one-way legs per city; the
  dashboard sums them into a round-trip total.
- **Economy only (2026-07-18, verified live)**: v3 ignores `trip_class`; v2
  `prices/latest` returns "Only economy trip class is supported". Business
  tracking is parked — no free API carries business fares. Do not re-add
  `trip_class` params.
- **Cached, not live**: prices are what Aviasales users found in the last
  ~48h. Great for trends/deals; always re-verify before booking. Return legs
  8 months out have little/no cache at first (first real scan: 7 NYC→TYO
  fares, 0 for OSA and the Mar 2027 returns) — coverage grows as departure
  approaches; empty days are normal, not errors.
- **Origin `NYC`** covers EWR + JFK + LGA; the actual airport of each offer
  is recorded per observation.
- **Quota**: 4 API calls/day (one per watch) — no quota concern. Travelpayouts
  asks to keep request rates modest; 0.3s pause between calls.
- **Cold start**: no alerts until a route has ≥5 scan days of history
  (`min_history_days`). Baseline = current month's scans, per user decision.
- **Y-1/Y-2/Y-3 comparison**: impossible to backfill (no free historical
  airfare data). The dashboard overlays previous years automatically as the
  DB accumulates them (first Y-1 in Sep 2027).
- **Re-alert suppression**: same route+cabin won't re-alert within 3 days
  unless the price got another ≥1% cheaper.
- **Mock mode** (`MOCK_SCAN=1` or `--mock`): full pipeline with generated
  data (uses `mock_*_window` grids in config), incl. a 30-day backfill on an
  empty DB. Delete `data/prices.sqlite` after mock testing.

## Outputs
- `data/prices.sqlite` — growing observation + deal history (committed).
- `docs/index.html` — dashboard (GitHub Pages once repo is public).
- Email alert when a deal fires.

## Edge cases
- Per-watch API errors are logged and skipped; the scan continues.
- Empty cache for a month pair → no observations that day (not an error).
- Mail failure → non-fatal; scan data and dashboard still commit.
