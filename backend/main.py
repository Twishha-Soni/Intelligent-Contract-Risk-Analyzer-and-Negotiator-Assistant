from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import base64
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

app = FastAPI()


@app.post('/playbook/ingest')
async def ingest_playbook(file: UploadFile = File(...)):
    # TODO: later wire it to ingestion folder
    return  {'chunks_indexed': 42}

@app.post('/contract/analyze')
async def analyze_contract(file: UploadFile = File(...)):
    # TODO: wire it to retrieve and generate folder

    clauses = [
        {"section": "7.2 Limitation of Liability", 
         "risk_level": "High",
         "rationale": "Liability cap excludes indirect damages entirely, exceeding playbook's standard 12-month fee cap.",
         "suggested_language": "Liability shall not exceed fees paid in the preceding 12 months, except for breaches of confidentiality."},
        {"section": "3.1 Auto-Renewal", 
         "risk_level": "Medium",
         "rationale": "90-day notice window is longer than the playbook's standard 30-day term.",
         "suggested_language": "Either party may terminate with 30 days' written notice prior to renewal."},
    ]
    low_risk_count = 6
    summary = ("This contract carries elevated risk in two areas: an uncapped liability clause "
    "and an extended auto-renewal notice period. Six clauses matched standard playbook terms.")

    pdf_bytes = generate_brief_pdf(summary, clauses, low_risk_count)
    return JSONResponse({
        'summary': summary,
        'clauses': clauses,
        'low_risk_count': low_risk_count,
        'brief_pdf_base64': base64.b64encode(pdf_bytes).decode('utf-8')
    })


def generate_brief_pdf(summary: str, clauses: list, low_risk_count: int) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = [Paragraph("Negotiation Brief", styles["Title"]), Spacer(1, 12),
    Paragraph(summary, styles["BodyText"]), 
    Spacer(1, 16),
    Paragraph(f"Flagged Clauses ({len(clauses)} Medium/High · {low_risk_count} Low)", styles["Heading2"]),
    Spacer(1, 8)]

    for c in clauses:
        color = colors.red if c['risk_level'] == 'High' else colors.orange
        story.append(Paragraph(f'<b><font color="{color.hexval()}">{c["section"]} — {c["risk_level"]}</font></b>', styles["Heading3"]))
        story.append(Paragraph(f'<b>Rationale:</b> {c["rationale"]}', styles["BodyText"]))
        story.append(Paragraph(f'<b>Suggested language:</b> {c["suggested_language"]}', styles["BodyText"]))
        story.append(Spacer(1, 10))

    doc.build(story)
    return buffer.getvalue()