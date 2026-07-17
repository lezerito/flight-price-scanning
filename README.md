# flight-price-scanning

Automated flight-price watcher: **NYC (EWR/JFK) ⇄ Japan (Tokyo/Osaka)**,
depart mid-September 2026, return March 2027. Scans daily on GitHub Actions,
records every price in SQLite, emails deal alerts in EUR with booking links
(economy + big business-class drops), and publishes an HTML dashboard.

## Setup (one time)

1. **Amadeus** (free): create an app at https://developers.amadeus.com →
   API Key + Secret.
2. **Travelpayouts** (free, optional): https://www.travelpayouts.com →
   API token.
3. **Gmail app password**: https://myaccount.google.com/apppasswords.
4. Add GitHub repo **Secrets** (Settings → Secrets and variables → Actions):
   `AMADEUS_CLIENT_ID`, `AMADEUS_CLIENT_SECRET`, `TRAVELPAYOUTS_TOKEN`,
   `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD`, `MAIL_TO`.
5. Enable **GitHub Pages**: Settings → Pages → Deploy from branch →
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
