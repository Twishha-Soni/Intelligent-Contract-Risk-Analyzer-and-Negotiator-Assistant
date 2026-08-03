from pydantic import BaseModel
from typing import Literal

class ClauseClassification(BaseModel):
    risk_level: Literal['Low', 'Medium', 'High']
    rationale: str
    suggested_language: str
    matched_playbook_ids: list[str]