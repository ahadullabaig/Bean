import os
import pytest
from unittest.mock import MagicMock, patch
from core.auditor import extract_facts
from core.ghostwriter import generate_narrative
from models.schemas import EventFacts, EventNarrative

@patch("google.generativeai.GenerativeModel")
@patch("os.getenv")
def test_auditor_logic(mock_getenv, mock_model_class):
    """Test auditor extraction flow with mocked API."""
    # Mock API key presence
    mock_getenv.return_value = "fake_key"
    
    # Mock the model instance and generate_content response
    mock_model_instance = MagicMock()
    mock_model_class.return_value = mock_model_instance
    
    mock_response = MagicMock()
    # Simulate the parsed response object that the SDK returns
    expected_facts = EventFacts(event_title="Mock Event", date="2024-01-01")
    mock_response.parsed = expected_facts
    
    mock_model_instance.generate_content.return_value = mock_response
    
    # Run the function
    result = extract_facts("Some raw text about Mock Event")
    
    # Verify inputs and outputs
    assert result.event_title == "Mock Event"
    assert result.date == "2024-01-01"
    mock_model_instance.generate_content.assert_called_once()
    
    # Verify configuration arguments
    args, kwargs = mock_model_instance.generate_content.call_args
    assert kwargs["generation_config"]["response_schema"] == EventFacts
    assert kwargs["generation_config"]["temperature"] == 0.0

@patch("google.generativeai.GenerativeModel")
@patch("os.getenv")
def test_ghostwriter_logic(mock_getenv, mock_model_class):
    """Test ghostwriter flow with mocked API."""
    mock_getenv.return_value = "fake_key"
    
    mock_model_instance = MagicMock()
    mock_model_class.return_value = mock_model_instance
    
    mock_response = MagicMock()
    expected_narrative = EventNarrative(
        executive_summary="Summary", 
        key_takeaways=["Point 1"]
    )
    mock_response.parsed = expected_narrative
    mock_model_instance.generate_content.return_value = mock_response
    
    facts = EventFacts(event_title="Test")
    result = generate_narrative(facts, "raw context")
    
    assert result.executive_summary == "Summary"
    assert len(result.key_takeaways) == 1
    
    # Verify temp is 0.3 for creativity
    args, kwargs = mock_model_instance.generate_content.call_args
    assert kwargs["generation_config"]["temperature"] == 0.3
