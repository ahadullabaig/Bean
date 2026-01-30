"""
UI Handlers - Input Processing with Caching.

These handlers process user inputs and delegate to core modules.
Caching is used to avoid redundant API calls for identical inputs.
"""
import streamlit as st
import hashlib
from core.auditor import extract_facts
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


def handle_audio_process(audio_file) -> EventFacts:
    """
    Processes audio file through the Auditor (Multimodal).
    
    NOTE: Currently a placeholder. Full implementation would:
    1. Send audio directly to Gemini's multimodal API
    2. Extract facts from the audio content
    """
    st.warning("Audio processing requires core update. Please use text for now.")
    return None
