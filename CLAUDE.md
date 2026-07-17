# flight-price-scanning — Project Instructions

Automated flight-price watcher: **NYC (EWR/JFK) ⇄ Japan (Tokyo/Osaka)**,
depart mid-September 2026, return March 2027, economy + business class.
Runs daily on GitHub Actions, accumulates its own price history (the
"learning"), emails deal alerts in EUR, publishes an HTML dashboard.

## Orientation (read in this order)

1. `workflows/flight_scan.md` — the SOP: pipeline order, design decisions,
   learned constraints (quota math, API quirks, cold-start rules).
2. `log.md` — dated project journal. **Read it to know where things stand;
   append an entry after every working session that changes anything.**
3. `config.json` — watched routes, date grids, deal thresholds.

## Key facts

- **Own git repo** (github.com/lezerito/flight-price-scanning, private),
  nested inside the CLAUDE-PROJECTS repo but independent of it. Commit and
  push here, never to the parent.
- **Runner**: `.github/workflows/daily-scan.yml`, daily 06:00 UTC. It runs
  `tools/run_daily.py` (scan → detect deals → email → rebuild dashboard)
  and commits `data/` + `docs/` back to `main`.
- **Data**: `data/prices.sqlite` is the system's memory — never delete it
  once real collection has started. `docs/index.html` is generated output;
  edit `tools/dashboard_template.html` instead.
- **Data source**: Travelpayouts/Aviasales v3 `prices_for_dates`, one query
  per one-way leg (cached prices, month granularity, economy only — the API
  rejects business class and >30-day round trips; see the SOP). Amadeus
  Self-Service is DEAD (decommissioned 2026-07-17) — do not reintroduce it.
- **Secrets** live only in `.env` (local) / GitHub Actions Secrets:
  `TRAVELPAYOUTS_TOKEN`, `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD`, `MAIL_TO`.
- **Quota**: 4 API calls/day (one per watch) — adding watches is cheap.
- **Testing without keys**: `python tools/run_daily.py --mock` (generates
  30 days of fake data on an empty DB). Delete `data/prices.sqlite`
  afterwards so mock data never mixes with real observations.
- **Dashboard checks**: after template changes, rebuild
  (`python tools/build_dashboard.py`) and screenshot both themes with
  headless Chrome before committing (see log.md 2026-07-18 for the command).

## Status markers to check first

- Are the GitHub secrets set? Until they are, scheduled runs exit cleanly
  with "nothing scanned" — no data is being collected.
- Is GitHub Pages enabled? Free plan requires the repo public; undecided
  so far. Without it the dashboard is only viewable from a local pull.
