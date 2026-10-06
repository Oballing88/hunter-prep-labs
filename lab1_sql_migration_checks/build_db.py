"""Builds a small SQLite database that pretends a customer-account migration
just ran: 'legacy_accounts' (old system) -> 'migrated_accounts' (new system).
A few defects are planted on purpose so the checks have something to find."""
import sqlite3

LEGACY = [
    # account_id, name,            region, monthly_rate
    (1001, "Alvarez, M",   "SD",  89.99),
    (1002, "Brooks, T",    "SD",  54.50),
    (1003, "Chen, L",      "OC",  120.00),
    (1004, "Diaz, R",      "OC",  75.25),
    (1005, "Evans, K",     "LV",  64.00),
    (1006, "Flores, J",    "LV",  99.00),
]

MIGRATED = [
    (1001, "Alvarez, M",   "SD",  89.99),
    (1002, "Brooks, T",    "SD",  54.50),
    (1003, "Chen, L",      None,  120.00),   # defect: region lost (NULL)
    (1004, "Diaz, R",      "OC",  -75.25),   # defect: sign flipped (out of range)
    (1004, "Diaz, R",      "OC",  -75.25),   # defect: duplicate row
    (1005, "Evans, K",     "LV",  46.00),    # defect: value changed in transit
    # defect: 1006 missing entirely
]


def build(path=":memory:"):
    conn = sqlite3.connect(path)
    conn.executescript("""
        DROP TABLE IF EXISTS legacy_accounts;
        DROP TABLE IF EXISTS migrated_accounts;
        CREATE TABLE legacy_accounts   (account_id INTEGER, name TEXT, region TEXT, monthly_rate REAL);
        CREATE TABLE migrated_accounts (account_id INTEGER, name TEXT, region TEXT, monthly_rate REAL);
    """)
    conn.executemany("INSERT INTO legacy_accounts VALUES (?,?,?,?)", LEGACY)
    conn.executemany("INSERT INTO migrated_accounts VALUES (?,?,?,?)", MIGRATED)
    conn.commit()
    return conn


if __name__ == "__main__":
    build("migration.db")
    print("migration.db written")
