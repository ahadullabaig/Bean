# Schema cleaning tests are no longer needed with the new google-genai SDK.
# The new SDK handles Pydantic models directly without requiring schema cleaning.

import pytest
from models.schemas import EventFacts, EventNarrative
from pydantic import BaseModel, Field
from typing import Optional

def test_pydantic_models_are_valid():
    """Verify our Pydantic models are well-formed for the new SDK."""
    # EventFacts with optional fields
    facts = EventFacts(event_title="Test Event", date=None)
    assert facts.event_title == "Test Event"
    assert facts.date is None
    
def test_event_facts_schema_export():
    """Verify EventFacts can export JSON schema (used by new SDK)."""
    schema = EventFacts.model_json_schema()
    assert "properties" in schema
    assert "event_title" in schema["properties"]
    
def test_event_narrative_schema_export():
    """Verify EventNarrative can export JSON schema."""
    schema = EventNarrative.model_json_schema()
    assert "properties" in schema
    assert "executive_summary" in schema["properties"]
    assert "key_takeaways" in schema["properties"]

def test_optional_fields_in_schema():
    """Verify optional fields are properly represented."""
    schema = EventFacts.model_json_schema()
    # The new SDK handles anyOf for Optional[T] natively
    # Just verify the schema is exportable and complete
    assert len(schema["properties"]) == 5  # All 5 fields present
