from dataclasses import dataclass
from typing import Optional
import fitz
import docx

@dataclass
class Line:
    text: str
    page_number: Optional[int]


def extract_lines(path: str) -> list[Line]:
    if path.lower().endswith('.pdf'):
        return extract_pdf_lines(path)
    elif path.lower().endswith('.docx'):
        return extract_docx_lines(path)

    raise ValueError(f'Unsupported file type: {path}')

def extract_pdf_lines(path: str) -> list[Line]:
    lines = []
    with fitz.open(path) as doc:
        for page_index, page in enumerate(doc, start=1):
            for raw_line in page.get_text('text').split('\n'):
                stripped = raw_line.strip()
                if stripped:
                    lines.append(Line(text=stripped, page_number=page_index))

    return lines

def extract_docx_lines(path: str) -> list[Line]:
    document = docx.Document(path)
    lines = []

    for para in document.paragraphs:
        stripped = para.text.strip()
        if stripped:
            lines.append(Line(text=stripped, page_number=None))

    return lines