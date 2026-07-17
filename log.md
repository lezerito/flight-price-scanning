# Project Log

One entry per date, newest first. Append an entry for every session that
changes code, config, data handling, or project status.

## 2026-07-18 (night, 3) — Paris → New York added as 5th watch

- One-off search PAR→NYC one-way Aug 25 – Sep 3 found €292–€396 (cheapest
  Sep 1 BVA→JFK self-transfer; best direct €322 Sep 3 ORY→EWR French Bee).
  User asked to track it permanently.
- Watch schema extended: `months` (list, for windows spanning months) and
  `depart_to` (upper day bound) alongside `depart_from`. Calendar view now
  renders one weekday grid per month spanned.
- Dashboard: third chart panel (PAR→NYC), title updated. First scan
  recorded 8 fare-days for the window.

## 2026-07-18 (night, 2) — outbound window narrowed to Sep 21–30

- User decision: departure must be **after Sep 20**. Added `depart_from:
  2026-09-21` to the outbound watches; scan filters day-level (the API only
  accepts whole months). Deleted the 10 already-collected out-of-scope
  fares (incl. the €371 Sep 15) so baselines reflect the real window.
- In-window cache is thinner: cheapest NYC→TYO after Sep 20 is currently
  €534 (Sep 23). Mock windows, dashboard texts, and search default updated.

## 2026-07-18 (night) — repo public, dashboard hosted on GitHub Pages

- User approved making this repo (and only this repo) public — repo
  visibility is per-repository, other repos unaffected (verified: it is the
  only public repo on the account). Secrets stay in Actions Secrets /
  gitignored `.env`, never in the repo.
- GitHub Pages enabled (main branch, `/docs`). Dashboard URL:
  https://lezerito.github.io/flight-price-scanning/ — refreshes
  automatically with each daily scan commit.

## 2026-07-18 (evening) — live: one-way legs, first real data, secrets set

- First live API tests forced two design corrections (both verified against
  the real API, documented in the SOP):
  1. v3 rejects round trips with a >30-day spread → the Sep→Mar trip is now
     **four one-way leg watches** (NYC→TYO/OSA Sep 2026; TYO/OSA→NYC Mar
     2027), with round-trip totals (out+back) computed on the dashboard.
  2. The API is **economy only** (v2: "Only economy trip class is
     supported"; v3 silently ignores trip_class) → business watches removed;
     feature parked until a free business-fare source exists.
- Dashboard reworked: leg tiles + round-trip total tiles, outbound/return
  panels, month-calendar heatmap (weekday grid) instead of the depart×return
  matrix; deals/emails handle one-way rows.
- **First real scan succeeded**: 7 NYC→TYO cached fares, cheapest €371
  (LGA→NRT 2026-09-15, F9). OSA + Mar 2027 returns empty — normal 8 months
  out. No alerts until 5 days of history (cold start).
- User provided credentials in `.env` (gitignored; app password quoted —
  spaces break `source` otherwise; mailer strips spaces before SMTP login).
  Gmail SMTP login verified. All 4 GitHub Actions secrets set via
  `gh secret set`.

## 2026-07-18 (later) — Amadeus decommissioned → Travelpayouts is primary

- User reported the Amadeus for Developers self-service portal was shut down
  on 2026-07-17. Verified: announced Feb 2026, new registrations closed
  spring 2026, all self-service keys deactivated. Enterprise portal is
  contract-only → not viable for a free system.
- Reworked the scanner around Travelpayouts/Aviasales v3 `prices_for_dates`:
  one query per watch with whole months (`departure_at=2026-09`,
  `return_at=2027-03`), `trip_class` 0/1 for economy/business, EUR, and
  aviasales booking links. 4 calls/day total (was ~48 with Amadeus grids).
- Removed `tools/amadeus_client.py` and all Amadeus references (secrets,
  workflow env, docs). Deal detection and dashboard no longer exclude
  `travelpayouts` observations — it is now the primary, comparable source.
- Added a 4th watch (NYC→OSA business — now cheap to track) and a 4th
  validated series color (yellow) to the dashboard.
- Caveat recorded in the SOP: prices are cached from real Aviasales searches
  (~48h window), not live quotes — re-verify before booking; sparse days are
  normal for a Sep→Mar long round trip.
- Secrets needed shrank to: `TRAVELPAYOUTS_TOKEN`, `GMAIL_ADDRESS`,
  `GMAIL_APP_PASSWORD`, `MAIL_TO`.

## 2026-07-18 — v1 built and deployed (awaiting API keys)

- Built the full v1 pipeline: `tools/scan.py` (Amadeus flight-offers over
  date grids + Travelpayouts month cache) → `data/prices.sqlite` →
  `tools/detect_deals.py` (rolling 30-day baseline; below 15th percentile
  or ≥25% eco / ≥30% biz under median) → `tools/send_alert.py` (Gmail SMTP,
  EUR, Google Flights links) → `tools/build_dashboard.py` → `docs/index.html`.
- Watches configured: NYC→TYO eco, NYC→OSA eco, NYC→TYO business; depart
  2026-09-10..25, return 2027-03-01..31; ~48 Amadeus calls/day (~1,450/mo
  vs 2,000 free quota).
- Verified end-to-end in mock mode (1,440 observations, deal detected,
  alert composed, dashboard rendered). Screenshot check (both themes) via:
  `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless
  --disable-gpu --window-size=1100,2000 --screenshot=out.png "file://$PWD/docs/index.html"`
  → fixed: business series moved to its own panel (scale squash), staggered
  line end-labels, x-tick collision. Mock DB deleted after testing.
- Created private repo github.com/lezerito/flight-price-scanning, pushed,
  daily Actions schedule live (06:00 UTC). Runs exit cleanly with a clear
  message until secrets are added.
- GitHub Pages blocked on free plan for private repos — decision pending:
  make repo public for a hosted dashboard URL, or view locally.
- **Next**: user adds Actions secrets (Amadeus, Travelpayouts, Gmail), then
  trigger *daily-flight-scan* manually for the first real scan; decide on
  Pages; consider switching `AMADEUS_ENV=production` once test data looks ok.
