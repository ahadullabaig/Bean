import json
import re

def parse_json_response(response):
    """
    Parses the response from Gemini.
    
    NOTE: With the new google-genai SDK, response.parsed is preferred.
    This function is kept for backward compatibility with tests.
    """
    # For new SDK, check for parsed attribute first
    if hasattr(response, "parsed") and response.parsed is not None:
        # If already a Pydantic model, return its dict representation
        if hasattr(response.parsed, "model_dump"):
            return response.parsed.model_dump()
        return response.parsed
    
    # Fallback to text parsing
    text = response.text
    if not text:
        raise ValueError("Response text is empty.")
        
    # Remove markdown code blocks
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        text = match.group(1)
        
    return json.loads(text)
