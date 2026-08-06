import json
from google import genai
import os
from dotenv import load_dotenv

from app.models.brief import NegotiationBrief
from app.services.Generate.prioritization import get_prioritized_rows

load_dotenv()
_client = genai.Client(api_key=os.getenv('GENERATOR_KEY'))


SYNTHESIS_PROMPT = """You are an experienced commercial contract attorney preparing a concise negotiation brief for an internal legal reviewer.

The clauses below have already been analyzed and ranked by risk severity.
High-risk clauses appear first, followed by Medium-risk clauses.
Do NOT change their order.

There are {low_count} Low-risk clauses that require no immediate negotiation and should only be acknowledged in the overview.

FLAGGED CLAUSES:
{clause_summaries}

Instructions:

Write an executive overview (2–3 sentences) that:
- summarizes the overall contractual risk profile,
- highlights the primary negotiation themes,
- mentions that {low_count} Low-risk clauses require no immediate attention.

For every flagged clause, generate one negotiation point in the exact order provided.

Each negotiation summary should:
- explain why negotiation is recommended,
- recommend one clear negotiation objective,
- remain under 40 words,
- use concise, professional language,
- avoid unnecessary legal jargon,
- be specific to the clause,
- avoid repeating advice across clauses,
- try to explain in simple words.

Do NOT:
- reorder clauses,
- omit clauses,
- invent facts,
- introduce new legal risks,
- discuss Low-risk clauses individually,
- copy the clause summary verbatim.

Return only JSON matching the required schema.
"""

def generate_brief(contract_id: str) -> tuple[NegotiationBrief, list[dict]]:
    flagged_rows, low_count = get_prioritized_rows(contract_id)

    prompt = SYNTHESIS_PROMPT.format(
        low_count=low_count,
        clause_summaries=_format_clauses(flagged_rows)
    )

    response = _client.models.generate_content(
        model='gemini-3.6-flash',
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