from app.models.playbook_chunk import PlaybookChunk
from app.services.Retrieve.segmentation import is_section_header
from app.utils.extraction import extract_pdf_lines

def chunk_playbook(path: str) -> list[PlaybookChunk]:
    lines = extract_pdf_lines(path)
    sections = pass1_split_playbook_sections(lines)

    chunks = []
    for i, (section_title, section_lines) in enumerate(sections, start=1):
        chunk_text = ' '.join(l.text for l in section_lines).strip()
        page_number = section_lines[0].page_number if section_lines else None
        chunks.append(PlaybookChunk(
            chunk_id=f'pb{i:03d}',
            section_title=section_title,
            chunk_text=chunk_text,
            page_number=page_number,
        ))
    return chunks


def pass1_split_playbook_sections(lines):
    sections = []
    current_title = 'PREAMBLE'
    current_lines = []
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
    

