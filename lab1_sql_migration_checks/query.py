import sqlite3, sys

conn = sqlite3.connect("migration.db")

for row in conn.execute(sys.argv[1]):
    print(row)