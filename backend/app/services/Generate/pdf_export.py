from collections import defaultdict
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.models.brief import NegotiationBrief

HIGH = colors.HexColor('#C0392B')
MEDIUM = colors.HexColor('#E67E22')
LOW = colors.HexColor('#27AE60')
HEADING = colors.HexColor('#2C3E50')
LABEL = colors.HexColor('#7F8C8D')
LIGHT_BG = colors.HexColor('#F8F9FA')

SEVERITY = {'High': 3, 'Medium': 2, 'Low': 1}
RISK_COLORS = {'High': HIGH, 'Medium': MEDIUM, 'Low': LOW}


def _escape(text: str) -> str:
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def _build_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        'title': ParagraphStyle(
            'BriefTitle',
            parent=base['Title'],
            fontName='Helvetica-Bold',
            fontSize=22,
            textColor=HEADING,
            spaceAfter=6,
        ),
        'subtitle': ParagraphStyle(
            'BriefSubtitle',
            parent=base['Normal'],
            fontName='Helvetica',
            fontSize=11,
            textColor=LABEL,
            spaceAfter=4,
        ),
        'section_heading': ParagraphStyle(
            'SectionHeading',
            parent=base['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=14,
            textColor=HEADING,
            spaceBefore=12,
            spaceAfter=6,
        ),
        'block_heading': ParagraphStyle(
            'BlockHeading',
            parent=base['Heading3'],
            fontName='Helvetica-Bold',
            fontSize=11,
            textColor=HEADING,
            spaceBefore=14,
            spaceAfter=6,
        ),
        'body': ParagraphStyle(
            'BriefBody',
            parent=base['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=HEADING,
        ),
        'label': ParagraphStyle(
            'BriefLabel',
            parent=base['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8,
            textColor=LABEL,
            spaceBefore=6,
            spaceAfter=2,
        ),
        'bullet': ParagraphStyle(
            'BriefBullet',
            parent=base['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            leftIndent=14,
            bulletIndent=0,
            textColor=HEADING,
        ),
        'clause_title': ParagraphStyle(
            'ClauseTitle',
            parent=base['Normal'],
            fontName='Helvetica-Bold',
            fontSize=11,
            textColor=HEADING,
        ),
        'risk_badge': ParagraphStyle(
            'RiskBadge',
            parent=base['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8,
            textColor=colors.white,
            alignment=TA_LEFT,
        ),
    }


def _risk_counts(flagged_rows: list[dict], low_count: int) -> dict[str, int]:
    high = sum(1 for r in flagged_rows if r['risk_level'] == 'High')
    medium = sum(1 for r in flagged_rows if r['risk_level'] == 'Medium')
    return {'High': high, 'Medium': medium, 'Low': low_count}


def _group_by_section(brief: NegotiationBrief, flagged_rows: list[dict]) -> list[tuple[str, list[dict]]]:
    points_by_id = {p.clause_id: p for p in brief.negotiation_points}
    rows_by_id = {r['clause_id']: r for r in flagged_rows}

    merged: list[dict] = []
    for point in brief.negotiation_points:
        row = rows_by_id.get(point.clause_id)
        if row is None:
            continue
        merged.append({**row, 'point': point})

    for row in flagged_rows:
        if row['clause_id'] not in points_by_id:
            continue
        if any(m['clause_id'] == row['clause_id'] for m in merged):
            continue
        merged.append({**row, 'point': points_by_id[row['clause_id']]})

    sections: dict[str, list[dict]] = defaultdict(list)
    for item in merged:
        sections[item['section']].append(item)

    ordered_sections = sorted(
        sections.items(),
        key=lambda pair: min(item['rowid'] for item in pair[1]),
    )

    grouped: list[tuple[str, list[dict]]] = []
    for section_name, items in ordered_sections:
        items.sort(key=lambda item: SEVERITY[item['risk_level']], reverse=True)
        grouped.append((section_name, items))
    return grouped


def _risk_summary_table(counts: dict[str, int], styles: dict[str, ParagraphStyle]) -> Table:
    rows = [
        [
            '',
            Paragraph('<b>High Risk Clauses</b>', styles['body']),
            Paragraph(str(counts['High']), styles['body']),
        ],
        [
            '',
            Paragraph('<b>Medium Risk Clauses</b>', styles['body']),
            Paragraph(str(counts['Medium']), styles['body']),
        ],
        [
            '',
            Paragraph('<b>Low Risk Clauses</b>', styles['body']),
            Paragraph(f"{counts['Low']} (Reviewed)", styles['body']),
        ],
    ]
    table = Table(rows, colWidths=[0.18 * inch, 4.2 * inch, 0.8 * inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), HIGH),
        ('BACKGROUND', (0, 1), (0, 1), MEDIUM),
        ('BACKGROUND', (0, 2), (0, 2), LOW),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.HexColor('#ECECEC')),
    ]))
    return table


def _bullet_list(items: list[str], styles: dict[str, ParagraphStyle]) -> list:
    flowables = []
    for item in items:
        flowables.append(Paragraph(f'• {_escape(item)}', styles['bullet']))
    return flowables


def _section_header(title: str, styles: dict[str, ParagraphStyle]) -> list:
    normalized = title.upper()
    return [
        Paragraph(_escape(normalized), styles['section_heading']),
        HRFlowable(width='100%', thickness=1, color=colors.HexColor('#DDE1E4'), spaceAfter=10),
    ]


def _clause_card(item: dict, styles: dict[str, ParagraphStyle]) -> Table:
    point = item['point']
    risk = point.risk_level
    risk_color = RISK_COLORS[risk]

    badge = Table(
        [[Paragraph(risk.upper(), styles['risk_badge'])]],
        colWidths=[0.65 * inch],
    )
    badge.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), risk_color),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))

    header = Table(
        [[badge, Paragraph(_escape(point.clause_title), styles['clause_title'])]],
        colWidths=[0.75 * inch, 5.9 * inch],
    )
    header.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))

    page_ref = item.get('page_number')
    page_line = []
    if page_ref is not None:
        page_line = [Paragraph(f'Contract page {_escape(str(page_ref))}', styles['subtitle'])]

    body_rows = [
        [Paragraph('Issue', styles['label'])],
        [Paragraph(_escape(item['rationale']), styles['body'])],
        [Paragraph('Recommendation', styles['label'])],
        [Paragraph(_escape(point.negotiation_summary), styles['body'])],
    ]
    if page_line:
        body_rows.append(page_line)

    card = Table(
        [[header]] + body_rows,
        colWidths=[6.65 * inch],
    )
    card.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BG),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#ECECEC')),
        ('LINEBEFORE', (0, 0), (0, -1), 4, risk_color),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    return card


def _build_cover_page(
    brief: NegotiationBrief,
    contract_id: str,
    counts: dict[str, int],
    styles: dict[str, ParagraphStyle],
) -> list:
    generated = datetime.now().strftime('%B %d, %Y')
    story = [
        Paragraph('Negotiation Brief', styles['title']),
        HRFlowable(width='100%', thickness=1.5, color=HEADING, spaceAfter=14),
        Paragraph(_escape(contract_id), styles['subtitle']),
        Paragraph(f'Generated: {generated}', styles['subtitle']),
        Spacer(1, 0.2 * inch),
        Paragraph('Risk Summary', styles['block_heading']),
        _risk_summary_table(counts, styles),
        Spacer(1, 0.15 * inch),
        Paragraph('Primary Focus', styles['block_heading']),
        *_bullet_list(brief.primary_focus, styles),
        Spacer(1, 0.1 * inch),
        Paragraph('Overall Recommendation', styles['block_heading']),
        Paragraph(_escape(brief.overall_recommendation), styles['body']),
        Spacer(1, 0.1 * inch),
        Paragraph('Overview', styles['block_heading']),
        Paragraph(_escape(brief.overview), styles['body']),
        PageBreak(),
    ]
    return story


def _build_body_pages(
    grouped_sections: list[tuple[str, list[dict]]],
    styles: dict[str, ParagraphStyle],
) -> list:
    if not grouped_sections:
        return [Paragraph('No flagged clauses to summarize.', styles['body']), PageBreak()]

    story: list = []
    for index, (section_name, items) in enumerate(grouped_sections):
        if index > 0:
            story.append(PageBreak())
        story.extend(_section_header(section_name, styles))
        for item in items:
            story.append(_clause_card(item, styles))
            story.append(Spacer(1, 0.12 * inch))
    story.append(PageBreak())
    return story


def _build_closing_page(brief: NegotiationBrief, styles: dict[str, ParagraphStyle]) -> list:
    story = [
        Paragraph('Overall Negotiation Strategy', styles['block_heading']),
        Paragraph(_escape(brief.overall_negotiation_strategy), styles['body']),
        Spacer(1, 0.12 * inch),
        Paragraph('Top Redlines', styles['block_heading']),
        *_bullet_list(brief.top_redlines, styles),
        Spacer(1, 0.12 * inch),
        Paragraph('Key Deal Breakers', styles['block_heading']),
        *_bullet_list(brief.deal_breakers, styles),
        Spacer(1, 0.35 * inch),
        Paragraph('Prepared By: ___________________________', styles['body']),
    ]
    return story


def export_brief_pdf(
    brief: NegotiationBrief,
    flagged_rows: list[dict],
    low_count: int,
    output_path: str,
    contract_id: str,
) -> str:
    styles = _build_styles()
    counts = _risk_counts(flagged_rows, low_count)
    grouped_sections = _group_by_section(brief, flagged_rows)

    story: list = []
    story.extend(_build_cover_page(brief, contract_id, counts, styles))
    story.extend(_build_body_pages(grouped_sections, styles))
    story.extend(_build_closing_page(brief, styles))

    doc = SimpleDocTemplate(
        output_path,
        pagesize=LETTER,
        topMargin=0.65 * inch,
        bottomMargin=0.65 * inch,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
    )
    doc.build(story)
    return output_path
