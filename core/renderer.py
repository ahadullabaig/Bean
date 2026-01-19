from io import BytesIO
from docxtpl import DocxTemplate
from models.schemas import FullReport

def sanitize_view_model(report: FullReport) -> dict:
    """
    Prepares the report data for the template.
    Handles None values, formatting, etc.
    """
    data = report.model_dump()
    
    # Flatten structure for easier template access if desired, 
    # or just clean up values.
    
    facts = data["facts"]
    narrative = data["narrative"]
    
    # Sanitize Facts
    for key, value in facts.items():
        if value is None:
            facts[key] = "N/A"
    
    # Ensure lists are not empty for iteration
    if not narrative["key_takeaways"]:
        narrative["key_takeaways"] = ["No specific takeaways recorded."]
        
    # We can perform date formatting here if needed
    # e.g., if facts['date'] is YYYY-MM-DD -> DD Month YYYY
    
    return {
        "facts": facts,
        "narrative": narrative,
        "executive_summary": narrative["executive_summary"], # Shortcut
        "key_takeaways": narrative["key_takeaways"]          # Shortcut
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
