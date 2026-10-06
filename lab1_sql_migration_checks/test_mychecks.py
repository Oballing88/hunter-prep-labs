import pytest
from build_db import build
from my_checks import find_duplicates, find_missing

@pytest.fixture
def conn():
    return build()   # fresh in-memory DB for every test

def test_duplicate_found(conn):
    assert find_duplicates(conn) == [(1004, 2)]

def test_missing_found(conn):
    assert find_missing(conn) == [(1006,)]