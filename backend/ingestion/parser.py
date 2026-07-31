import re
from dataclasses import dataclass
import fitz
import docx

NUMBERING_PATTERN = re.compile(r"^\s*(\d+(\.\d+)*|\([a-z]\)|\([ivx]+\))\s*[\.\)]?\s*", re.IGNORECASE)


@dataclass
class Block:
    text: str
    is_heading: bool
    