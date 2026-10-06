# Bug reports — lab 1 SQL migration checks

Rebuilt `migration.db` with `build_db.py` on 2026-09-29, then ran each finding query through `query.py`. Both fail every time. One defect per report.

Working directory for every step: `Career/Research/hunter-labs/lab1_sql_migration_checks`.

---

## Duplicate account 1004

**Title:** Migration: account 1004 duplicated in migrated_accounts.

**Severity:** Medium. Diaz, R is still in the new system, so this is not a vanished customer. Two rows for the same `account_id` make any count, join, or sum count that account twice.

**Steps to reproduce:**

1. Run `python build_db.py`. It writes `migration.db` and prints `migration.db`.
2. Run the duplicate-key query:

```text
python query.py "SELECT account_id, COUNT(*) FROM migrated_accounts GROUP BY account_id HAVING COUNT(*) > 1"
```

**Expected:** No rows. Each `account_id` appears once. Legacy has one row for 1004 (Diaz, R).

**Actual:** One row. Account 1004 is stored twice.

**Evidence:**

```text
(1004, 2)
```

---

## Missing account 1006

**Title:** Migration: account 1006 missing from migrated_accounts.

**Severity:** High. Flores, J is in `legacy_accounts` and absent from `migrated_accounts`. The customer vanished completely.

**Steps to reproduce:**

1. Run `python build_db.py`. It writes `migration.db` and prints `migration.db`.
2. Run the missing-row query:

```text
python query.py "SELECT l.account_id FROM legacy_accounts l LEFT JOIN migrated_accounts m ON m.account_id = l.account_id WHERE m.account_id IS NULL"
```

**Expected:** No rows. Every legacy account, including 1006 (Flores, J, LV, monthly rate 99.00), is in `migrated_accounts`.

**Actual:** One row. Account 1006 never arrived.

**Evidence:**

```text
(1006,)
```
