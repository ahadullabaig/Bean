import json
import re

def parse_json_response(response):
    """
    Parses the response from Gemini.
    Attempts to access response.parsed (if available).
    Falls back to parsing response.text, handling Markdown code blocks.
    """
    try:
        # Check if the attribute exists and is not None
        if hasattr(response, "parsed") and response.parsed is not None:
            return response.parsed
    except Exception:
        pass
    
    text = response.text
    if not text:
        raise ValueError("Response text is empty.")
        
    # Remove markdown code blocks
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        text = match.group(1)
        
    return json.loads(text)
