"""Reusable SQL data-quality checks. Each returns the offending rows (empty = pass)."""

def null_values(conn, table, column):
    return conn.execute(f"SELECT * FROM {table} WHERE {column} IS NULL").fetchall()


def duplicate_keys(conn, table, key):
    return conn.execute(
        f"SELECT {key}, COUNT(*) FROM {table} GROUP BY {key} HAVING COUNT(*) > 1"
    ).fetchall()


def out_of_range(conn, table, column, low, high):
    return conn.execute(
        f"SELECT * FROM {table} WHERE {column} < ? OR {column} > ?", (low, high)
    ).fetchall()


def missing_after_migration(conn):
    """Rows in the old system that never arrived in the new one (LEFT JOIN)."""
    return conn.execute("""
        SELECT l.account_id FROM legacy_accounts l
        LEFT JOIN migrated_accounts m ON m.account_id = l.account_id
        WHERE m.account_id IS NULL
    """).fetchall()


def changed_values(conn, column):
    """Rows whose value differs between old and new system."""
    return conn.execute(f"""
        SELECT DISTINCT l.account_id, l.{column}, m.{column}
        FROM legacy_accounts l JOIN migrated_accounts m ON m.account_id = l.account_id
        WHERE l.{column} IS NOT m.{column}
    """).fetchall()


def row_counts(conn):
    old = conn.execute("SELECT COUNT(*) FROM legacy_accounts").fetchone()[0]
    new = conn.execute("SELECT COUNT(*) FROM migrated_accounts").fetchone()[0]
    return old, new
