"""Email deal alerts via Gmail SMTP (app password).

If GMAIL_ADDRESS / GMAIL_APP_PASSWORD / MAIL_TO are not set, prints the email
body instead of sending — the pipeline never fails on missing mail config.
"""
import os
import smtplib
from email.mime.text import MIMEText

CABIN_LABEL = {"ECONOMY": "Economy", "BUSINESS": "Business"}


def render_html(deals):
    rows = []
    for d in deals:
        airports = ""
        if d.get("origin_airport"):
            airports = f" ({d['origin_airport']}→{d['destination_airport']})"
        rows.append(f"""
        <div style="border:1px solid #ddd;border-radius:8px;padding:14px;margin:10px 0">
          <div style="font-size:18px;font-weight:bold">
            {d['origin']} → {d['destination']}{airports} —
            {CABIN_LABEL.get(d['cabin'], d['cabin'])}: €{d['price_eur']:,.0f}
          </div>
          <div style="color:#555;margin:4px 0">
            Depart {d['depart_date']} · Return {d['return_date']}
            · Airline: {d.get('airline') or 'n/a'}</div>
          <div style="color:#0a7d32;margin:4px 0">
            {d['pct_below_median']}% below recent median
            (€{d['baseline_median']:,.0f}) — {d['reason']}</div>
          <a href="{d['deep_link']}">Open in Google Flights →</a>
        </div>""")
    return ("<html><body style='font-family:sans-serif'>"
            "<h2>✈️ Flight deal alert</h2>" + "".join(rows) +
            "<p style='color:#999;font-size:12px'>flight-price-scanning · "
            "prices in EUR, verify before booking</p></body></html>")


def send(deals):
    if not deals:
        print("no deals to send")
        return
    subject_bits = [f"{d['origin']}→{d['destination']} €{d['price_eur']:,.0f}"
                    for d in deals[:2]]
    subject = "✈️ Flight deal: " + " | ".join(subject_bits)
    html = render_html(deals)

    addr = os.environ.get("GMAIL_ADDRESS")
    pwd = os.environ.get("GMAIL_APP_PASSWORD")
    to = os.environ.get("MAIL_TO") or addr
    if not (addr and pwd and to):
        print("mail not configured — would have sent:")
        print(subject)
        for d in deals:
            print(f"  {d['origin']}->{d['destination']} {d['cabin']} "
                  f"€{d['price_eur']:,.0f} ({d['reason']})")
        return

    msg = MIMEText(html, "html")
    msg["Subject"] = subject
    msg["From"] = addr
    msg["To"] = to
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(addr, pwd)
        s.sendmail(addr, [to], msg.as_string())
    print(f"alert sent to {to}: {subject}")
