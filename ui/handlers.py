"""
UI Handlers - Input Processing with Caching.

These handlers process user inputs and delegate to core modules.
Caching is used to avoid redundant API calls for identical inputs.
"""
import streamlit as st
import hashlib
from typing import Optional
from core.auditor import extract_facts
from core.llm import get_gemini_client, DEFAULT_MODEL, RateLimitError, AuthenticationError, is_rate_limit_error, is_auth_error
from google.genai.errors import ClientError
from models.schemas import EventFacts


def _compute_text_hash(text: str) -> str:
    """Compute a stable hash for caching purposes."""
    return hashlib.md5(text.encode()).hexdigest()


@st.cache_data(show_spinner=False)
def _cached_extract_facts(text_hash: str, text: str, api_key: str) -> dict:
    """
    Cached fact extraction - converts to dict for Streamlit serialization.
    
    Uses text_hash as the primary cache key to detect duplicate inputs.
    Returns a dict that will be converted back to EventFacts.
    """
    facts = extract_facts(text, api_key=api_key)
    return facts.model_dump()


def handle_text_process(raw_text: str, api_key: str) -> EventFacts:
    """
    Processes raw text through the Auditor.
    Results are cached to avoid redundant API calls for identical input.
    """
    with st.spinner("The Auditor is reading your notes..."):
        text_hash = _compute_text_hash(raw_text)
        facts_dict = _cached_extract_facts(text_hash, raw_text, api_key)
        return EventFacts(**facts_dict)


def handle_audio_process(audio_file, api_key: str) -> Optional[EventFacts]:
    """
    Processes audio file through Gemini's multimodal API.
    
    Uses Gemini's native audio understanding to:
    1. Transcribe the audio content
    2. Extract structured facts directly from the audio
    
    This is a single-pass approach (audio → facts) rather than
    audio → text → facts, which is more efficient and accurate.
    
    Args:
        audio_file: Streamlit audio input (BytesIO-like with .read())
        api_key: Gemini API key for this session
        
    Returns:
        EventFacts if successful, None if extraction fails
        
    Raises:
        RateLimitError: If API rate limit is hit
        AuthenticationError: If API key is invalid
    """
    from pydantic import ValidationError
    
    client = get_gemini_client(api_key)
    
    # Read audio bytes
    audio_bytes = audio_file.read()
    
    # Prepare the prompt for audio fact extraction
    prompt = """You are a strict data entry clerk. Listen to the audio recording about an event and extract specific event details.

RULES:
1. Extract strictly from what you hear. Do not infer or guess.
2. If a field is not mentioned, leave it as null (None).
3. Return the result in the specified JSON structure.
4. Pay close attention to lists (Coordinators, Judges, Winners).
5. For Winners, extract team name, members, and prize if mentioned.

Extract the following fields:
- event_title: The official title of the event
- date: The date of the event (YYYY-MM-DD format if possible)
- venue: The physical location where the event took place
- speaker_name: Name of the primary speaker or guest
- attendance_count: Number of attendees (as integer)
- organizer: Organizing body (default: "IEEE RIT Student Branch")
- student_coordinators: List of student coordinator names
- faculty_coordinators: List of faculty coordinator names
- judges: List of judges
- volunteer_count: Number of volunteers (as integer)
- target_audience: Target audience (e.g., '2nd Year CSE')
- mode: Mode of conduction: 'Online', 'Offline', or 'Hybrid'
- agenda: Short agenda or flow of the event
- media_link: Link to photos or registration
- winners: List of winners with place, prize_money, team_name, and members
"""
    
    try:
        # Use Gemini's multimodal capability with audio
        response = client.models.generate_content(
            model=DEFAULT_MODEL,
            contents=[
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": "audio/wav",  # Streamlit audio_input provides WAV
                                "data": audio_bytes
                            }
                        }
                    ]
                }
            ],
            config={
                "response_mime_type": "application/json",
                "response_schema": EventFacts,
                "temperature": 0.0
            }
        )
    except ClientError as e:
        if is_rate_limit_error(e):
            raise RateLimitError(
                "API rate limit exceeded. Please wait 1 minute before trying again.",
                retry_after=60
            )
        if is_auth_error(e):
            raise AuthenticationError(
                "Invalid API key. Please check your key and try again."
            )
        raise
    
    # Best case: SDK auto-parsed into Pydantic
    if response.parsed is not None:
        return response.parsed
    
    # Fallback: Try manual JSON parsing
    if response.text:
        try:
            return EventFacts.model_validate_json(response.text)
        except ValidationError as e:
            raise ValueError(f"Failed to parse audio extraction response: {e}")
    
    raise ValueError("LLM returned empty response for audio input")

