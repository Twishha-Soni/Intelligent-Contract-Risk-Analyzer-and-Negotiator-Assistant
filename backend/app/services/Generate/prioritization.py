from app.database.db import get_connection

SEVERITY = {'High': 3, 'Medium': 2, 'Low': 1}

def get_prioritized_rows(contract_id_filter: str | None = None) -> tuple[list[dict], int]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM clause_classifications ORDER BY rowid ASC"
    ).fetchall()
    conn.close()

    all_rows = [dict(r) for r in rows]
    low_count = sum(1 for r in all_rows if r['risk_level'] == 'Low')
    flagged = [r for r in all_rows if r['risk_level'] in ('High', 'Medium')]

    flagged.sort(key=lambda r: SEVERITY[r['risk_level']], reverse=True)
    return flagged, low_count