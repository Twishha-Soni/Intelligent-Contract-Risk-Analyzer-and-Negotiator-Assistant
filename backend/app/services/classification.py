import json
from google import genai
import os
from dotenv import load_dotenv

from app.models.clause import Clause
from app.models.classification import ClauseClassification
from app.database.db import get_connection

load_dotenv()
_client = genai.Client(api_key=os.getenv('CLASSIFICATION_KEY'))

CLASSIFICATION_PROMPT = """You are reviewing a contract clause against a company playbook.

CLAUSE (section: {section}):
{clause_text}

RETRIEVED PLAYBOOK CONTEXT:
{playbook_context}

Classify this clause's risk level (Low/Medium/High) based on how it deviates from the playbook's standard position. Provide a rationale grounded in the specific playbook entries above, suggested replacement/fallback language, and list the chunk_ids of the playbook entries you actually relied on.
"""

def classify_and_store(clause: Clause, playbook_chunks: list[dict]) -> ClauseClassification:
    result = classify_clause(clause, playbook_chunks)

    conn = get_connection()
    conn.execute(
        """INSERT OR REPLACE INTO clause_classifications
        (clause_id, section, clause_text, page_number, risk_level,
        rationale, suggested_language, matched_playbook_ids)
        VALUES (?,?,?,?,?,?,?,?)""",
        (
            clause.clause_id,
            clause.section,
            clause.clause_text,
            clause.page_number,
            result.risk_level,
            result.rationale,
            result.suggested_language,
            json.dumps(result.matched_playbook_ids)
        )
    )
    conn.commit()
    conn.close()
    return result

def classify_clause(clause: Clause, playbook_chunks: list[dict]) -> ClauseClassification:
    prompt = CLASSIFICATION_PROMPT.format(
        section=clause.section,
        clause_text=clause.clause_text,
        _format_playbook_context=_format_playbook_context(playbook_chunks)
    )

    response = _client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config={
            'response_mime_type': 'application/json',
            'response_schema': ClauseClassification
        }
    )

    return ClauseClassification.model_validate(json.loads(response.text))

def _format_playbook_context(chunks: list[dict]) -> str:
    return '\n\n'.join(
        f"[{c['chunk_id']}] ({c['category']} - {c['section_title']}:\n{c['chunk_text']})"
        for c in chunks
    )
    

