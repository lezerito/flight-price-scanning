# Project Log

One entry per date, newest first. Append an entry for every session that
changes code, config, data handling, or project status.

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
