import re
from io import BytesIO
from docxtpl import DocxTemplate
from models.schemas import FullReport


def sanitize_jinja_input(value: str) -> str:
    """
    Escapes Jinja2 control characters to prevent template injection.
    Replaces {{ }} and {% %} with safe alternatives.
    """
    if not isinstance(value, str):
        return value
    # Escape Jinja2 delimiters
    value = re.sub(r'\{\{', '{ {', value)
    value = re.sub(r'\}\}', '} }', value)
    value = re.sub(r'\{%', '{ %', value)
    value = re.sub(r'%\}', '% }', value)
    return value


def sanitize_view_model(report: FullReport) -> dict:
    """
    Prepares the report data for the template.
    Handles None values, formatting, and security sanitization.
    """
    data = report.model_dump()
    
    facts = data["facts"]
    narrative = data["narrative"]
    
    # Sanitize Facts - handle None and escape Jinja2 characters
    for key, value in facts.items():
        if value is None:
            facts[key] = "N/A"
        elif isinstance(value, str):
            facts[key] = sanitize_jinja_input(value)
    
    # Ensure lists are not empty for iteration
    list_fields = ["student_coordinators", "faculty_coordinators", "judges", "winners"]
    for field in list_fields:
        if field in facts and not facts[field]:
             facts[field] = []

    if not narrative["key_takeaways"]:
        narrative["key_takeaways"] = ["No specific takeaways recorded."]
    else:
        narrative["key_takeaways"] = [
            sanitize_jinja_input(t) for t in narrative["key_takeaways"]
        ]
    
    # Sanitize executive summary
    narrative["executive_summary"] = sanitize_jinja_input(
        narrative["executive_summary"]
    )
    
    # Format hashtags with # prefix
    hashtags = narrative.get("hashtags", [])
    formatted_hashtags = " ".join([f"#{tag}" for tag in hashtags]) if hashtags else ""
        
    return {
        "facts": facts,
        "narrative": narrative,
        "executive_summary": narrative["executive_summary"],
        "key_takeaways": narrative["key_takeaways"],
        "hashtags": formatted_hashtags
    }


def render_report(report: FullReport, template_path: str = "master_template.docx") -> BytesIO:
    """
    Renders the report into a DOCX file in memory.
    """
    doc = DocxTemplate(template_path)
    context = sanitize_view_model(report)
    
    doc.render(context)
    
    file_stream = BytesIO()
    doc.save(file_stream)
    file_stream.seek(0)
    
    return file_stream


def render_pdf(report: FullReport) -> BytesIO:
    """
    Renders the report as a professional PDF using reportlab.
    
    This is a native PDF generation (not DOCX conversion) for portability.
    No external dependencies like LibreOffice required.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.colors import HexColor
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=0.75*inch, leftMargin=0.75*inch,
                           topMargin=0.75*inch, bottomMargin=0.75*inch)
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=HexColor('#1a365d'),
        spaceAfter=12
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=HexColor('#2c5282'),
        spaceBefore=16,
        spaceAfter=8
    )
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        leading=16,
        spaceAfter=8
    )
    bullet_style = ParagraphStyle(
        'CustomBullet',
        parent=styles['Normal'],
        fontSize=11,
        leftIndent=20,
        spaceAfter=4
    )
    
    # Build document content
    story = []
    facts = report.facts
    narrative = report.narrative
    
    # Title
    story.append(Paragraph(facts.event_title or "Event Report", title_style))
    story.append(Spacer(1, 12))
    
    # Metadata table
    metadata = [
        ["Date", facts.date or "N/A"],
        ["Venue", facts.venue or "N/A"],
        ["Organizer", facts.organizer or "N/A"],
        ["Mode", facts.mode or "N/A"],
        ["Attendance", str(facts.attendance_count) if facts.attendance_count else "N/A"],
    ]
    if facts.speaker_name:
        metadata.append(["Speaker", facts.speaker_name])
    
    t = Table(metadata, colWidths=[1.5*inch, 4.5*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), HexColor('#e2e8f0')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cbd5e0')),
    ]))
    story.append(t)
    story.append(Spacer(1, 20))
    
    # Executive Summary
    story.append(Paragraph("Executive Summary", heading_style))
    story.append(Paragraph(narrative.executive_summary, body_style))
    story.append(Spacer(1, 12))
    
    # Key Takeaways
    story.append(Paragraph("Key Takeaways", heading_style))
    for takeaway in narrative.key_takeaways:
        story.append(Paragraph(f"• {takeaway}", bullet_style))
    story.append(Spacer(1, 12))
    
    # Coordinators
    if facts.student_coordinators or facts.faculty_coordinators:
        story.append(Paragraph("Coordinators", heading_style))
        if facts.student_coordinators:
            story.append(Paragraph(f"<b>Students:</b> {', '.join(facts.student_coordinators)}", body_style))
        if facts.faculty_coordinators:
            story.append(Paragraph(f"<b>Faculty:</b> {', '.join(facts.faculty_coordinators)}", body_style))
    
    # Winners (if any)
    if facts.winners:
        story.append(Paragraph("Winners", heading_style))
        for winner in facts.winners:
            members_str = f" ({', '.join(winner.members)})" if winner.members else ""
            prize_str = f" - {winner.prize_money}" if winner.prize_money else ""
            story.append(Paragraph(f"• <b>{winner.place}:</b> {winner.team_name or 'N/A'}{members_str}{prize_str}", bullet_style))
    
    doc.build(story)
    buffer.seek(0)
    return buffer
