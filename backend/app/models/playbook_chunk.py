from dataclasses import dataclass
from typing import Optional

@dataclass
class PlaybookChunk:
    chunk_id: str
    section_title: str
    chunk_text: str
    page_number: Optional[int]