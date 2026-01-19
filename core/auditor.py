from core.llm import get_gemini_model, get_clean_schema
from models.schemas import EventFacts
from utils.parsing import parse_json_response

def extract_facts(text: str) -> EventFacts:
    """
    Uses a strict, low-temperature LLM call to extract specific event facts.
    """
    model = get_gemini_model()
    
    prompt = f"""
    You are a strict data entry clerk. Your job is to extract specific event details from the raw text provided below.
    
    RULES:
    1. Extract strictly from the text. Do not infer or guess.
    2. If a field is missing, leave it as null (None).
    3. Return the result in the specified JSON structure.
    
    Raw Text:
    {text}
    """
    
    # Use generation_config to enforce structured output if needed, 
    # but for now, we rely on the Pydantic type response_schema support in newer SDKs 
    # or simple prompt engineering + response_mime_type="application/json".
    # Since gemini-2.0-flash-exp supports strict schema generation:
    
    response = model.generate_content(
        prompt,
        generation_config={
            "response_mime_type": "application/json",
            "response_schema": get_clean_schema(EventFacts),
            "temperature": 0.0
        }
    )
    
    # The SDK automatically handles the parsing into the schema object if passed correctly,
    # or provides a JSON string we can parse.
    # Note: As of current SDK, we often get a parsed object or need to load it. 
    # Assuming the SDK returns an object conforming to the schema or a text we parse.
    # For robustnes with current typical usage:
    
    data = parse_json_response(response)
    return EventFacts(**data)
