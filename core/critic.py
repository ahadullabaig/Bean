from typing import List
from core.llm import get_gemini_client, DEFAULT_MODEL

def check_consistency(original_text: str, report_text: str) -> List[str]:
    """
    Compares the generated report against the original text to find hallucinations.
    Returns a list of warnings (strings). Returns empty list if clean.
    """
    client = get_gemini_client()
    
    prompt = f"""
    You are a strict Compliance Auditor.
    Compare the Source Text against the Generated Report.
    
    SOURCE TEXT:
    {original_text}
    
    GENERATED REPORT:
    {report_text}
    
    INSTRUCTIONS:
    1. Identify any concrete facts (dates, names, numbers, venues) in the Report that are NOT supported by the Source Text.
    2. Ignore stylistic changes or professional phrasing.
    3. Ignore facts that are "N/A" or generic placeholders.
    4. If you find an unsupported fact, list it as a short bullet point.
    5. If the report is consistent, return "SAFE".
    
    Return ONLY the list of issues, or "SAFE".
    """
    
    response = client.models.generate_content(
        model=DEFAULT_MODEL,
        contents=prompt
    )
    
    if not response.text:
        return []
        
    text = response.text.strip()
    
    if "SAFE" in text:
        return []
    
    # Split by newlines and clean up
    issues = [line.strip("- *") for line in text.split("\n") if line.strip()]
    return issues
