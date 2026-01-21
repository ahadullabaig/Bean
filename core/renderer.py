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
        
    return {
        "facts": facts,
        "narrative": narrative,
        "executive_summary": narrative["executive_summary"],
        "key_takeaways": narrative["key_takeaways"]
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
