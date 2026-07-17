# Workflow: Flight Price Scan (NYC ⇄ Japan)

## Objective
Collect flight prices daily for EWR/JFK → Japan (depart mid-Sep 2026, return
Mar 2027), build a price history, detect deals (economy + business-class
drops), email alerts in EUR with booking links, and publish an HTML dashboard.

## Inputs
- `config.json` — watched routes, date windows/grids, deal thresholds.
- Secrets in `.env` locally, GitHub Actions Secrets in the cloud:
  `AMADEUS_CLIENT_ID`, `AMADEUS_CLIENT_SECRET`, `TRAVELPAYOUTS_TOKEN`,
  `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD`, `MAIL_TO`.

## Tools (run in this order — or just `tools/run_daily.py` which chains them)
1. `tools/scan.py` — Amadeus flight-offers over the date grids + Travelpayouts
   month caches → appends to `data/prices.sqlite`.
2. `tools/detect_deals.py` — compares today's best vs rolling 30-day history
   (current month, since there's no older data yet).
3. `tools/send_alert.py` — Gmail SMTP alert; prints instead of sending when
   mail secrets are absent.
4. `tools/build_dashboard.py` — regenerates `docs/index.html` (GitHub Pages).

## Scheduling
`.github/workflows/daily-scan.yml` runs everything daily at 06:00 UTC and
commits `data/` + `docs/` back to the repo. This is how the system keeps
collecting/learning with no machine of ours running.

## Design decisions & constraints (learned)
- **Origin `NYC`** covers EWR + JFK + LGA in one Amadeus query; the actual
  airport of each offer is recorded per observation.
- **Quota**: Amadeus free tier ≈ 2,000 calls/month. Current grids ≈ 48
  calls/day ≈ 1,450/month. If a grid is widened, re-do this math first.
- **Amadeus test env** returns cached, sometimes sparse data. Once validated,
  switch to production keys (also free) by setting repo variable
  `AMADEUS_ENV=production`.
- **Travelpayouts caveat**: cached prices assume typical trip lengths, not a
  6-month stay → stored with `source='travelpayouts'` and **excluded** from
  deal baselines and the dashboard series; broad-signal only.
- **Cold start**: no alerts until a route has ≥5 scan days of history
  (`min_history_days`). Baseline = current month's scans, per user decision
  (no historical DB exists yet).
- **Y-1/Y-2/Y-3 comparison**: impossible to backfill (no free historical
  airfare data). The dashboard is built to overlay previous years
  automatically as the DB accumulates them (first Y-1 in Sep 2027).
- **Re-alert suppression**: same route+cabin won't re-alert within 3 days
  unless the price got another ≥1% cheaper.
- **Mock mode** (`MOCK_SCAN=1` or `--mock`): full pipeline with generated
  data, incl. a 30-day backfill on an empty DB. Never mixes with real data
  in a committed DB — delete `data/prices.sqlite` after mock testing.

## Outputs
- `data/prices.sqlite` — growing observation + deal history (committed).
- `docs/index.html` — dashboard (GitHub Pages).
- Email alert when a deal fires.

## Edge cases
- Amadeus 429 → client backs off 3s and retries once; per-call errors are
  logged and skipped, the scan continues.
- Empty offer response for a date pair → simply no observation that day.
- Mail failure → non-fatal; scan data and dashboard still commit.
