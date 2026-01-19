import streamlit as st
from core.auditor import extract_facts
from models.schemas import EventFacts

def handle_text_process(raw_text: str) -> EventFacts:
    """Processes raw text through the Auditor."""
    with st.spinner("The Auditor is reading your notes..."):
        facts = extract_facts(raw_text)
    return facts
    
# For audio, we would integrate the multimodal call here.
# Since we haven't implemented a dedicated audio-to-text or audio-auditor in core yet,
# we will stick to text for the MVP step or mock the audio handling if needed.
# However, the plan mentioned "handle_audio_input". 
# Let's add a placeholder that would call Gemini with audio data.

def handle_audio_process(audio_file) -> EventFacts:
    """
    Processes audio file through the Auditor (Multimodal).
    
    NOTE: core/auditor.py currently expects string. 
    We would need to update core/auditor.py to handle parts/blobs 
    or transcribe first. 
    
    For Phase 3 MVP, we will assume the User transcribes or we convert to text using Gemini.
    """
    # This checks if we need to update auditor.py to support audio.
    # The master plan says "Send audio directly to Gemini".
    # We will defer this implementation detail or implementation update to "Phase 5 Polish" 
    # or handle it as a TODO if `core` doesn't support it yet.
    # For now, let's just return None or simulated data to not break the UI flow.
    st.warning("Audio processing requires core update. Please use text for now.")
    return None
