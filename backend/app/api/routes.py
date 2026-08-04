import tempfile, os
from fastapi import APIRouter, UploadFile, HTTPException
from fastapi.responses import FileResponse
import time

from app.utils.extraction import extract_lines
from app.services.segmentation import segment_contract
from app.services.retrieval import retrieve_playbook_context
from app.services.classification import classify_and_store
from app.services.brief_synthesis import generate_brief
from app.services.pdf_export import export_brief_pdf
from app.database.db import get_connection
from app.models.feedback import FeedbackIn

router = APIRouter()

@router.post('/contracts/analyze')
async def analyze_contract(file: UploadFile):
    suffix = '.pdf' if file.filename.lower().endswith('.pdf') else '.docx'
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        clauses = segment_contract(tmp_path)
        results = []
        for clause in clauses:
            playbook_chunks = retrieve_playbook_context(clause)
            classification = classify_and_store(clause, playbook_chunks)
            results.append({
                "clause_id": clause.clause_id,
                "section": clause.section,
                "clause_text": clause.clause_text,
                "risk_level": classification.risk_level,
                "rationale": classification.rationale,
                "suggested_language": classification.suggested_language,
                "matched_playbook_ids": classification.matched_playbook_ids,
            })
            time.sleep(5)
        return {'clause_count': len(results), 'clauses': results}
    finally:
        os.unlink(tmp_path)

@router.get('/contracts/brief')
async def get_brief():
    brief, flagged_rows = generate_brief()
    if not flagged_rows:
        raise HTTPException(status_code=404, detail='No flagged clauses to summarize')

    output_path = 'app/database/negotiation_brief.pdf'
    export_brief_pdf(brief, output_path)
    return FileResponse(output_path, media_type='application/pdf', filename='negotiation_brief.pdf')

@router.post('/feedback')
async def submit_feedback(feedback: FeedbackIn):
    conn = get_connection()
    conn.execute(
        "INSERT INTO feedback (clause_id, action, edited_suggestion) VALUES (?,?,?)",
        (feedback.clause_id, feedback.action, feedback.edited_suggestion)
    )
    conn.commit()
    conn.close()
    return {'status': 'recorded'}