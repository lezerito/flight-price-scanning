# flight-price-scanning

Automated flight-price watcher: **NYC (EWR/JFK) ⇄ Japan (Tokyo/Osaka)**,
depart mid-September 2026, return March 2027. Scans daily on GitHub Actions,
records every price in SQLite, emails deal alerts in EUR with booking links
(economy + big business-class drops), and publishes an HTML dashboard.

Data source: **Travelpayouts/Aviasales Data API** (free; cached prices from
real searches). Amadeus Self-Service was decommissioned on 2026-07-17 and is
no longer an option.

## Setup (one time)

1. **Travelpayouts** (free): register at https://www.travelpayouts.com →
   API token (profile → API).
2. **Gmail app password**: https://myaccount.google.com/apppasswords.
3. Add GitHub repo **Secrets** (Settings → Secrets and variables → Actions):
   `TRAVELPAYOUTS_TOKEN`, `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD`, `MAIL_TO`.
4. Enable **GitHub Pages**: Settings → Pages → Deploy from branch →
   `main` / `docs/`. The dashboard then lives at
   `https://<user>.github.io/flight-price-scanning/`.

The daily workflow runs at 06:00 UTC (Actions tab → *daily-flight-scan* →
*Run workflow* to trigger manually).

## Run locally

```bash
pip install -r requirements.txt
cp .env.example .env          # fill in keys
set -a; source .env; set +a
python tools/run_daily.py     # full pipeline
python tools/run_daily.py --mock   # test without API keys (fake data)
open docs/index.html
```

After mock testing, delete `data/prices.sqlite` so real data starts clean.

See `workflows/flight_scan.md` for the full SOP and design decisions.
