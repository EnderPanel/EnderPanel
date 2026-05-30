import os
import sys

from database import engine
import sqlalchemy

def run_migrations():
    print("Testing migrations")
    migrations = [
        ("servers", "swap_mb", "INTEGER NOT NULL DEFAULT 512"),
    ]
    with engine.connect() as conn:
        for table, column, definition in migrations:
            rows = conn.execute(sqlalchemy.text(f"PRAGMA table_info({table})")).fetchall()
            print("ROWS:", rows)
            existing = {row[1] for row in rows}
            if column not in existing:
                print("executing alter")
                conn.execute(sqlalchemy.text(f"ALTER TABLE {table} ADD COLUMN {column} {definition}"))
                conn.commit()
                print("done")
            else:
                print("already existing")

run_migrations()
