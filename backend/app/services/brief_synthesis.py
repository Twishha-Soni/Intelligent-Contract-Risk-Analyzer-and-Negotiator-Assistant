import json
from google import genai
import os
from dotenv import load_dotenv

from app.models.brief import NegotiationBrief
from app.services.prioritization import get_prioritized_rows

load_dotenv()
_client = genai.Client(api_key=os.getenv('GENERATOR_KEY'))


SYNTHESIS_PROMPT = """You are drafting a one-page negotiation brief for a contract reviewer.

The clauses below are already ranked by risk severity (High first, then Medium) — do not reorder them. There are also {low_count} Low-risk clauses not requiring attention.

FLAGGED CLAUSES:
{clause_summaries}

Write a brief 2-3 sentence overview, then a negotiation_summary (1-2 sentences, actionable) for each clause in the same order given.
"""

def generate_brief() -> tuple[NegotiationBrief, list[dict]]:
    flagged_rows, low_count = get_prioritized_rows()

    prompt = SYNTHESIS_PROMPT.format(
        low_count=low_count,
        clause_summaries=_format_clauses(flagged_rows)
    )

    response = _client.models.generate_content(
        model='gemini-3.1-flash-lite',
        contents=prompt,
        config={
            'response_mime_type': 'application/json',
            'response_schema': NegotiationBrief
        }
    )

    brief = NegotiationBrief.model_validate(json.loads(response.text))
    return brief, flagged_rows

def _format_clauses(rows: list[dict]) -> str:
    return '\n\n'.join(
        f"[{r['clause_id']}] {r['section']} - {r['risk_level']}\n"
        f"Rationale: {r['rationale']}\nSuggested language: {r['suggested_language']}"
        for r in rows
    )