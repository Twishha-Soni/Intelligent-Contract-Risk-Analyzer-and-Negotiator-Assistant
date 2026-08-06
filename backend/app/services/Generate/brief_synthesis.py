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

There are {low_count} Low-risk clauses that require no immediate negotiation and should only be acknowledged in the overview.

FLAGGED CLAUSES:
{clause_summaries}

Instructions:

Write an executive overview (2–3 sentences) that:
- summarizes the overall contractual risk profile,
- highlights the primary negotiation themes,
- mentions that {low_count} Low-risk clauses require no immediate attention.

Provide primary_focus: 3–5 cross-cutting negotiation themes (e.g. Liability Cap, IP Ownership, Payment Terms).

Provide overall_recommendation: 1–2 sentences stating the recommended negotiation posture and top priorities.

Provide overall_negotiation_strategy: a short paragraph describing how to approach the negotiation.

Provide top_redlines: 3–5 must-win negotiation items as concise bullet strings.

Provide deal_breakers: 2–4 non-negotiable walk-away issues as concise bullet strings.

For every flagged clause, generate exactly one negotiation point.
Include every flagged clause exactly once; order in JSON does not matter.
Each point must include the matching clause_id from the input.

For each negotiation point:
- clause_title: a short descriptive label (6 words or fewer), no clause IDs,
- negotiation_summary: recommendation only (one clear negotiation objective),
  under 40 words, concise and professional, specific to the clause,
  not copied verbatim from the rationale.

Do NOT:
- omit clauses,
- invent facts,
- introduce new legal risks,
- discuss Low-risk clauses individually,
- copy the clause rationale verbatim into negotiation_summary.

Return only JSON matching the required schema.
"""


def generate_brief(contract_id: str) -> tuple[NegotiationBrief, list[dict], int]:
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
    return brief, flagged_rows, low_count


def _format_clauses(rows: list[dict]) -> str:
    return '\n\n'.join(
        f"Clause ID: {r['clause_id']}\n"
        f"Section: {r['section']} - {r['risk_level']}\n"
        f"Rationale: {r['rationale']}\n"
        f"Suggested language: {r['suggested_language']}"
        for r in rows
    )
