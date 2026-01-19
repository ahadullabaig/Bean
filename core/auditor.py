from core.llm import get_gemini_client, DEFAULT_MODEL
from models.schemas import EventFacts

def extract_facts(text: str) -> EventFacts:
    """
    Uses a strict, low-temperature LLM call to extract specific event facts.
    """
    client = get_gemini_client()
    
    prompt = f"""
    You are a strict data entry clerk. Your job is to extract specific event details from the raw text provided below.
    
    RULES:
    1. Extract strictly from the text. Do not infer or guess.
    2. If a field is missing, leave it as null (None).
    3. Return the result in the specified JSON structure.
    
    Raw Text:
    {text}
    """
    
    response = client.models.generate_content(
        model=DEFAULT_MODEL,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": EventFacts,
            "temperature": 0.0
        }
    )
    
    # The new SDK auto-parses into Pydantic instances via response.parsed
    return response.parsed
