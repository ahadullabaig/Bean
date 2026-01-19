from core.llm import get_gemini_client, DEFAULT_MODEL
from models.schemas import EventFacts, EventNarrative

def generate_narrative(facts: EventFacts, raw_context: str) -> EventNarrative:
    """
    Uses a creative, medium-temperature LLM call to write the narrative sections.
    """
    client = get_gemini_client()
    
    facts_dict = facts.model_dump(exclude_none=True)
    
    prompt = f"""
    You are a professional Ghostwriter for the IEEE Student Branch.
    Write an Executive Summary and Key Takeaways based strictly on the facts provided.
    
    FACTS (These are strict truth):
    {facts_dict}
    
    CONTEXT/TONE (Use this for style, but do not invent new names/dates):
    {raw_context}
    
    RULES:
    1. Use professional, academic English (Third person).
    2. Do NOT add new entity facts (like numbers, dates, or names) that are not in the FACTS dictionary.
    3. Transform simple statements into professional prose.
    4. Provide the output in the specified JSON structure.
    """
    
    response = client.models.generate_content(
        model=DEFAULT_MODEL,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": EventNarrative,
            "temperature": 0.3
        }
    )
    
    return response.parsed
