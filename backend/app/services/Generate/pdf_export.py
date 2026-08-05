from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch

from app.models.brief import NegotiationBrief

def export_brief_pdf(brief: NegotiationBrief, output_path: str, contract_id: str) -> str:
    doc = SimpleDocTemplate(output_path, pagesize=LETTER,
                            topMargin=0.6 * inch, bottomMargin=0.6 * inch)
    styles = getSampleStyleSheet()
    story = [
        Paragraph(f'Negotiation Brief for {contract_id}', styles['Title']),
        Spacer(1, 12),
        Paragraph(brief.overview, styles['BodyText']),
        Spacer(1, 16)
    ]

    for point in brief.negotiation_points:
        story.append(
            Paragraph(
                f"<b>{point.clause_id} - {point.section} ({point.risk_level})</b>",
                styles['Heading4']
            )
        )
        story.append(Paragraph(point.negotiation_summary, styles['BodyText']))
        story.append(Spacer(1,10))

    doc.build(story)
    return output_path