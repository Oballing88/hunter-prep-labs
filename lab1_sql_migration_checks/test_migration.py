"""Go/no-go data checks for a migration. Every test here FINDS a planted defect,
so each one asserts on exactly what it found. In real use you'd assert the
result is empty, and a non-empty result would block the release."""
import pytest
from build_db import build
import checks


@pytest.fixture
def conn():
    connection = build()          # fresh in-memory DB per test
    yield connection
    connection.close()


def test_row_counts_match_but_hide_problems(conn):
    old, new = checks.row_counts(conn)
    assert (old, new) == (6, 6)   # equal counts... but that hides real problems!


def test_no_null_regions(conn):
    assert checks.null_values(conn, "migrated_accounts", "region") == [
        (1003, "Chen, L", None, 120.0)
    ]


def test_no_duplicate_account_ids(conn):
    assert checks.duplicate_keys(conn, "migrated_accounts", "account_id") == [(1004, 2)]


def test_rates_in_valid_range(conn):
    bad = checks.out_of_range(conn, "migrated_accounts", "monthly_rate", 0, 500)
    assert {row[0] for row in bad} == {1004}


def test_every_legacy_account_arrived(conn):
    assert checks.missing_after_migration(conn) == [(1006,)]


def test_values_unchanged_in_transit(conn):
    changed = checks.changed_values(conn, "monthly_rate")
    assert sorted(row[0] for row in changed) == [1004, 1005]


def test_clean_data_passes_all_checks():
    """The same checks on clean data return nothing: that's a 'go'."""
    import sqlite3
    c = sqlite3.connect(":memory:")
    c.executescript("""
        CREATE TABLE legacy_accounts   (account_id INTEGER, name TEXT, region TEXT, monthly_rate REAL);
        CREATE TABLE migrated_accounts (account_id INTEGER, name TEXT, region TEXT, monthly_rate REAL);
        INSERT INTO legacy_accounts   VALUES (1, 'A', 'SD', 10.0), (2, 'B', 'OC', 20.0);
        INSERT INTO migrated_accounts VALUES (1, 'A', 'SD', 10.0), (2, 'B', 'OC', 20.0);
    """)
    assert checks.null_values(c, "migrated_accounts", "region") == []
    assert checks.duplicate_keys(c, "migrated_accounts", "account_id") == []
    assert checks.out_of_range(c, "migrated_accounts", "monthly_rate", 0, 500) == []
    assert checks.missing_after_migration(c) == []
    assert checks.changed_values(c, "monthly_rate") == []
