import re
from backend.utils.extraction import Line, extract_lines
from backend.models.clause import Clause

# ---- Orchestration ----
def segment_contract(path: str) -> list[Clause]:
    lines = extract_lines(path)
    sections = pass1_split_sections(lines)
    clauses: list[Clause] = []
    clause_counter = 0

    for section_title, section_lines in sections:
        for marker, chunk_lines in pass2_split_subclauses(section_lines):
            chunk_text = ' '.join(l.text for l in chunk_lines).strip()
            page_number = chunk_lines[0].page_number if chunk_lines else None
            word_count = len(chunk_text.split())

            if marker is not None or word_count < FALLBACK_WORD_THRESHOLD:
                clause_counter += 1
                clauses.append(Clause(
                    clause_id=f'c{clause_counter:04d}',
                    section=section_title,
                    clause_text=chunk_text,
                    page_number=page_number,
                    source_type='numbered' if marker else 'unstructured',
                    raw_marker=marker,
                ))
            else:
                for group_text in sentence_group_fallback(chunk_text):
                    clause_counter += 1
                    clauses.append(Clause(
                        clause_id=f'c{clause_counter:04d}',
                        section=section_title,
                        clause_text=group_text,
                        page_number=page_number,
                        source_type='sentence_group',
                        raw_marker=None,
                    ))
    return clauses



# ---- Pass 1: section headers ----
SECTION_HEADER_PATTERNS = [
    re.compile(r'^(ARTICLE|SECTION)\s+([IVXLCivxlc0-9]+)\b[\.:\-–)]?\s*(.*)$', re.IGNORECASE),
    re.compile(r'^(\d{1,2})[\.\)]\s+([A-Z][A-Z0-9 ,&/\-]{2,})$'),
]

def is_section_header(text: str) -> bool:
    for pattern in SECTION_HEADER_PATTERNS:
        if pattern.match(text):
            return True
    words = text.split()
    if 1 <= len(words) <= 8 and text == text.upper() and not text.endswith(('.', ',')):
        return True
    return False

def pass1_split_sections(lines: list[Line]) -> list[tuple[str, list[Line]]]:
    sections = []
    current_title = "RECITALS"
    current_lines: list[Line] = []
    for line in lines:
        if is_section_header(line.text):
            if current_lines:
                sections.append((current_title, current_lines))
            current_title = line.text
            current_lines = []
        else:
            current_lines.append(line)
    if current_lines:
        sections.append((current_title, current_lines))

    return sections



# ---- Pass 2: Sub-clause numbering ----
SUBCLAUSE_PATTERNS = [
    re.compile(r'^(\d+\.\d+(?:\.\d+)?)\s+(.*)$'),    # 7.1, 7.1.2
    re.compile(r'^\(([a-zA-Z]{1,3}|[ivxlc]{1,4})\)\s+(.*)$'),  # (a), (i)
    re.compile(r'^(\d+)\.\s+(.*)$'),                    # 1.
    re.compile(r'^[•\-\*]\s+(.*)$'),                    # bullets
]

def match_subclause(text: str) -> tuple[str | None, str | None]:
    for pattern in SUBCLAUSE_PATTERNS:
        m = pattern.match(text)
        if m:
            groups = m.groups()
            marker = groups[0] if len(groups) > 1 else None
            body = groups[-1]
            return marker, body
    return None, None


def pass2_split_subclauses(section_lines: list[Line]) -> list[tuple[str | None, list[Line]]]:
    chunks = []
    current_marker: str | None = None
    current_lines: list[Line] = []
    for line in section_lines:
        marker, body = match_subclause(line.text)
        if marker is not None:
            if current_lines:
                chunks.append((current_marker, current_lines))
            current_marker = marker
            current_lines = [Line(text=body, page_number=line.page_number)]
        else:
            current_lines.append(line)
    if current_lines:
        chunks.append((current_marker, current_lines))
    return chunks


# ---- Fallback: sentence grouping for long, unnumbered chunks ----
SENTENCE_SPLIT = re.compile(r'(?<=[.!?])\s+(?=[A-Z(])')
FALLBACK_WORD_THRESHOLD = 120
GROUP_TARGET_WORDS = 80

def sentence_group_fallback(text: str) -> list[str]:
    sentences = [s.strip() for s in SENTENCE_SPLIT.split(text) if s.strip()]
    groups, current, current_words = [], [], 0
    for sentence in sentences:
        current.append(sentence)
        current_words += len(sentence.split())
        if current_words >= GROUP_TARGET_WORDS:
            groups.append(" ".join(current))
            current, current_words = [], 0
    if current:
        groups.append(' '.join(current))
    return groups or [text]