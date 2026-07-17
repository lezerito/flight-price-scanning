# flight-price-scanning — Project Instructions

Automated flight-price watcher, live and collecting daily. Five one-way
watches: **NYC (EWR/JFK) → Tokyo/Osaka** (depart Sep 21–30, 2026),
**Tokyo/Osaka → NYC** (return any day Mar 2027), and **Paris → New York**
(Aug 25 – Sep 3, 2026). Runs on GitHub Actions, accumulates its own price
history (the "learning"), emails deal alerts in EUR, publishes an HTML
dashboard with round-trip totals for the Japan trip.

**Dashboard**: https://lezerito.github.io/flight-price-scanning/
**Alerts**: whereislm@gmail.com, only when a deal fires (no daily digest).

## Orientation (read in this order)

1. `workflows/flight_scan.md` — the SOP: pipeline order, design decisions,
   learned API constraints (one-way-only legs, economy-only, cache quirks).
2. `log.md` — dated project journal. **Read it to know where things stand;
   append an entry after every working session that changes anything.**
3. `config.json` — watches, deal thresholds. Watch schema: `month` (single)
   or `months` (list, for windows spanning months), optional day-level
   `depart_from`/`depart_to` bounds (the API only accepts whole months),
   `panel` (which dashboard chart panel: out/ret/par), `mock_window`.

## Key facts

- **Own git repo** (github.com/lezerito/flight-price-scanning, **public** —
  the user's only public repo; all their other repos must stay private),
  nested inside the CLAUDE-PROJECTS repo but independent of it. Commit and
  push here, never to the parent. GitHub Pages serves `main`/`docs/`.
- **Runner**: `.github/workflows/daily-scan.yml`, daily 06:00 UTC. It runs
  `tools/run_daily.py` (scan → detect deals → email → rebuild dashboard)
  and commits `data/` + `docs/` back to `main`; Pages redeploys on push.
- **Data source**: Travelpayouts/Aviasales v3 `prices_for_dates`, one query
  per watch-month, `one_way=true`, cached prices (~48h old, re-verify before
  booking). Hard limits verified live: rejects round trips with >30-day
  spread (hence one-way legs) and is **economy-only** (business rejected —
  parked; do not re-add `trip_class`). Amadeus Self-Service is DEAD
  (decommissioned 2026-07-17) — do not reintroduce it. ~6 API calls/day.
- **Data**: `data/prices.sqlite` is the system's memory — never delete it
  (real collection started 2026-07-17). `docs/index.html` is generated;
  edit `tools/dashboard_template.html` instead.
- **Secrets** (all set, live): `.env` locally (gitignored; app password
  must stay quoted), GitHub Actions Secrets in the cloud —
  `TRAVELPAYOUTS_TOKEN`, `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD`, `MAIL_TO`.
  Update via `gh secret set NAME --body "..."`.
- **Deal rules**: alert when today's best ≤ 15th percentile of the rolling
  30-day history or ≥25% below its median; needs ≥5 scan days per route
  (cold start); 3-day re-alert suppression unless ≥1% cheaper.
- **Empty days are normal**: far-out windows (Mar 2027 returns) have thin
  cache; coverage grows as departure approaches. Zero observations for a
  watch is not an error.
- **Testing without burning API cache**: `python tools/run_daily.py --mock`
  (generates 30 days of fake data on an empty DB). Delete
  `data/prices.sqlite` afterwards — never let mock rows mix with the real
  history. Real DB present? Don't run mock at all.
- **Dashboard checks**: after template changes, rebuild
  (`python tools/build_dashboard.py`) and screenshot both themes with
  headless Chrome before committing (command in log.md 2026-07-18). Chart
  colors are the validated 4-slot palette — run the dataviz validator if
  slots are added.

## When returning to this project

- Check the Actions tab (or `gh run list --workflow=daily-flight-scan`) —
  scheduled runs should be green; investigate any red run via its logs.
- `log.md` top entry = last known state. Diff `observed_at` dates in the DB
  against today to confirm collection never silently stopped.
- Dates: the runner records `observed_at` in UTC; local manual runs use
  local time — adjacent-date skew is harmless, avoid manual runs near
  06:00 UTC.
