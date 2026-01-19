import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

def get_gemini_client():
    """
    Configures and returns a Gemini client instance.
    Raises ValueError if GEMINI_API_KEY is missing.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables.")
    
    return genai.Client(api_key=api_key)

# Default model to use across the application
DEFAULT_MODEL = "gemini-2.5-flash"
