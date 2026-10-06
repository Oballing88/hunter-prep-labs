def find_duplicates(conn):
    return conn.execute(
        "SELECT account_id, COUNT(*) FROM migrated_accounts "
        "GROUP BY account_id HAVING COUNT(*) > 1"
    ).fetchall()
def find_missing(conn):
    return conn.execute(
        "SELECT l.account_id FROM legacy_accounts l "
        "LEFT JOIN migrated_accounts m ON m.account_id = l.account_id "
        "WHERE m.account_id IS NULL"
    ).fetchall()
