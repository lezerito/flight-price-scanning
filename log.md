# Project Log

One entry per date, newest first. Append an entry for every session that
changes code, config, data handling, or project status.

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
