"""SQLite storage for flight price observations and detected deals."""
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "prices.sqlite")

SCHEMA = """
CREATE TABLE IF NOT EXISTS observations (
    id INTEGER PRIMARY KEY,
    observed_at TEXT NOT NULL,          -- ISO date of the scan
    source TEXT NOT NULL,               -- amadeus | travelpayouts | mock
    origin TEXT NOT NULL,               -- IATA city code searched (NYC)
    destination TEXT NOT NULL,          -- IATA city code searched (TYO/OSA)
    origin_airport TEXT,                -- actual airport in the offer (EWR/JFK)
    destination_airport TEXT,
    depart_date TEXT NOT NULL,
    return_date TEXT,
    cabin TEXT NOT NULL,                -- ECONOMY | BUSINESS
    price_eur REAL NOT NULL,
    airline TEXT,
    deep_link TEXT
);
CREATE INDEX IF NOT EXISTS idx_obs_route ON observations
    (origin, destination, cabin, observed_at);

CREATE TABLE IF NOT EXISTS deals (
    id INTEGER PRIMARY KEY,
    detected_at TEXT NOT NULL,
    observation_id INTEGER NOT NULL REFERENCES observations(id),
    reason TEXT NOT NULL,
    baseline_median REAL,
    pct_below_median REAL,
    emailed INTEGER DEFAULT 0
);
"""


def connect():
    path = os.path.abspath(DB_PATH)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def insert_observation(conn, obs: dict) -> int:
    cols = ("observed_at", "source", "origin", "destination", "origin_airport",
            "destination_airport", "depart_date", "return_date", "cabin",
            "price_eur", "airline", "deep_link")
    cur = conn.execute(
        f"INSERT INTO observations ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
        [obs.get(c) for c in cols],
    )
    return cur.lastrowid
