import tempfile, os
from fastapi import APIRouter, UploadFile, HTTPException
from fastapi.responses import FileResponse
import time

from app.utils.extraction import extract_lines
from app.services.Ingest.playbook_indexer import index_playbook
from app.services.Retrieve.segmentation import segment_contract
from app.services.Retrieve.retrieval import retrieve_playbook_context
from app.services.Generate.classification import classify_and_store
from app.services.Generate.brief_synthesis import generate_brief
from app.services.Generate.pdf_export import export_brief_pdf
from app.database.vector_store import get_client, ensure_collection, COLLECTION_NAME

router = APIRouter()

@router.post('/playbook/upload')
async def upload_playbook(file: UploadFile):
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail='Playbook must be a PDF')

    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        count = index_playbook(tmp_path)
        return {'status': 'ingested', 'chunk_count': count}
    finally:
        os.unlink(tmp_path)

@router.delete('/playbook')
async def remove_playbook():
    client = get_client()
    client.delete_collection(COLLECTION_NAME)
    ensure_collection(client)
    return {'status': 'removed'}

def _playbook_is_ingested() -> bool:
    client = get_client()
    info = client.get_collection(COLLECTION_NAME)
    return info.points_count > 0

@router.post('/contracts/analyze')
async def analyze_contract(file: UploadFile):
    if not _playbook_is_ingested():
        raise HTTPException(status_code=409, detail='No playbook is ingested yet - upload a playbook first')
    
    contract_id = os.path.splitext(file.filename)[0]
    suffix = '.pdf' if file.filename.lower().endswith('.pdf') else '.docx'
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        clauses = segment_contract(tmp_path)
        results = []
        for clause in clauses:
            playbook_chunks = retrieve_playbook_context(clause)
            classification = classify_and_store(clause, playbook_chunks, contract_id)
            results.append({
                "clause_id": clause.clause_id,
                "section": clause.section,
                "clause_text": clause.clause_text,
                "risk_level": classification.risk_level,
                "rationale": classification.rationale,
                "suggested_language": classification.suggested_language,
                "matched_playbook_ids": classification.matched_playbook_ids,
            })
            time.sleep(3)
        return {'contract_id': contract_id, 'clause_count': len(results), 'clauses': results}
    finally:
        os.unlink(tmp_path)

@router.get('/contracts/{contract_id}/brief')
async def get_brief(contract_id: str):
    brief, flagged_rows = generate_brief(contract_id)
    if not flagged_rows:
        raise HTTPException(status_code=404, detail='No flagged clauses to summarize')

    output_path = f'app/database/tempDB/negotiation_brief_{contract_id}.pdf'
    export_brief_pdf(brief, output_path, contract_id)
    return FileResponse(output_path, media_type='application/pdf', filename=f'{contract_id}_negotiation_brief.pdf')