import sqlite3
from pathlib import Path

DB_PATH = Path('app/database/contracts.db')

def init_db() -> None:
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS clause_classifications (
            clause_id TEXT PRIMARY KEY,
            section TEXT NOT NULL,
            clause_text TEXT NOT NULL,
            page_number INTERGER,
            risk_level TEXT NOT NULL,
            rationale TEXT NOT NULL,
            suggested_language TEXT NOT NULL,
            matched_playbook_ids TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
