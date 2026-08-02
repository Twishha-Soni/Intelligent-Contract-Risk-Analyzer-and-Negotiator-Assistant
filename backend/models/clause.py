from dataclasses import dataclass
from typing import Optional

@dataclass
class Clause:
    clause_id: str
    section: str
    clause_text: str
    page_number: Optional[int]
    source_type: str
    raw_marker: Optional[str] = None