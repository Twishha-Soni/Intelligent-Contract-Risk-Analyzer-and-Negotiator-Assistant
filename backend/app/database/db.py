import sqlite3
from pathlib import Path

DB_PATH = Path('app/database/contracts.db')

def init_db() -> None:
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS clause_classifications (
            contract_id TEXT NOT NULL,
            clause_id TEXT NOT NULL,
            section TEXT NOT NULL,
            clause_text TEXT NOT NULL,
            page_number INTERGER,
            risk_level TEXT NOT NULL,
            rationale TEXT NOT NULL,
            suggested_language TEXT NOT NULL,
            matched_playbook_ids TEXT NOT NULL,
            PRIMARY KEY (contract_id, clause_id)
        )
    """)
    conn.commit()
    conn.close()

def init_feedback_table() -> None:
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        contract_id TEXT NOT NULL,
        clause_id TEXT NOT NULL,
        action TEXT NOT NULL,       --'accept' | 'reject' | 'edit'
        edited_suggestion TEXT,     -- populated only when action='edit'
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (contract_id, clause_id) REFERENCES clause_classifications(contract_id, clause_id)
        )
    """)
    conn.commit()
    conn.close()

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
