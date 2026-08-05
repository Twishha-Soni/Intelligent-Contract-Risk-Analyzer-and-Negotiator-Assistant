from pydantic import BaseModel
from typing import Optional, Literal

class FeedbackIn(BaseModel):
    contract_id: str
    clause_id: str
    action: Literal['accept', 'reject', 'edit']
    edited_suggestion: Optional[str] = None