"""
Unit tests for the Auditor (Fact Extraction) module.
Tests cover: valid extraction, empty input, self-correction, and error handling.
"""
import pytest
from unittest.mock import patch, Mock, MagicMock
from pydantic import ValidationError

from core.auditor import extract_facts
from models.schemas import EventFacts


class TestAuditorExtraction:
    """Tests for the extract_facts function."""
    
    def test_extract_facts_valid_input(self, sample_raw_text, mock_auditor_response, sample_event_facts):
        """Test that valid input returns correctly parsed EventFacts."""
        with patch('core.auditor.get_gemini_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_auditor_response
            mock_get_client.return_value = mock_client
            
            result = extract_facts(sample_raw_text)
            
            # Verify the result is an EventFacts instance
            assert isinstance(result, EventFacts)
            assert result.event_title == sample_event_facts.event_title
            assert result.date == sample_event_facts.date
            assert result.venue == sample_event_facts.venue
            assert result.attendance_count == sample_event_facts.attendance_count
    
    def test_extract_facts_calls_gemini_with_correct_config(self, sample_raw_text, mock_auditor_response):
        """Test that Gemini is called with temperature 0.0 and correct schema."""
        with patch('core.auditor.get_gemini_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_auditor_response
            mock_get_client.return_value = mock_client
            
            extract_facts(sample_raw_text)
            
            # Verify the API was called with correct parameters
            call_args = mock_client.models.generate_content.call_args
            config = call_args.kwargs.get('config', {})
            
            assert config.get('temperature') == 0.0
            assert config.get('response_mime_type') == 'application/json'
            assert config.get('response_schema') == EventFacts
    
    def test_extract_facts_empty_input(self, mock_auditor_response):
        """Test behavior with empty input string."""
        with patch('core.auditor.get_gemini_client') as mock_get_client:
            # Simulate response with minimal/empty facts
            empty_facts = EventFacts()
            mock_response = Mock()
            mock_response.parsed = empty_facts
            
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_response
            mock_get_client.return_value = mock_client
            
            result = extract_facts("")
            
            # Should still return an EventFacts object (with None/default values)
            assert isinstance(result, EventFacts)
    
    def test_extract_facts_preserves_list_fields(self, sample_raw_text):
        """Test that list fields (coordinators, judges) are correctly extracted."""
        with patch('core.auditor.get_gemini_client') as mock_get_client:
            facts_with_lists = EventFacts(
                event_title="Hackathon",
                student_coordinators=["Alice", "Bob"],
                faculty_coordinators=["Prof. Smith"],
                judges=["Judge1", "Judge2", "Judge3"]
            )
            mock_response = Mock()
            mock_response.parsed = facts_with_lists
            
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_response
            mock_get_client.return_value = mock_client
            
            result = extract_facts(sample_raw_text)
            
            assert len(result.student_coordinators) == 2
            assert len(result.judges) == 3


class TestAuditorSelfCorrection:
    """Tests for the self-correction loop."""
    
    def test_self_correction_on_none_parsed(self, sample_raw_text, sample_event_facts):
        """Test that manual parsing is attempted when response.parsed is None."""
        with patch('core.auditor.get_gemini_client') as mock_get_client:
            mock_response = Mock()
            mock_response.parsed = None
            mock_response.text = sample_event_facts.model_dump_json()
            
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_response
            mock_get_client.return_value = mock_client
            
            result = extract_facts(sample_raw_text)
            
            # Should successfully parse via fallback
            assert isinstance(result, EventFacts)
            assert result.event_title == sample_event_facts.event_title
    
    def test_raises_after_max_retries(self, sample_raw_text):
        """Test that ValueError is raised when parsing fails."""
        with patch('core.auditor.get_gemini_client') as mock_get_client:
            mock_response = Mock()
            mock_response.parsed = None
            mock_response.text = "invalid json {"
            
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_response
            mock_get_client.return_value = mock_client
            
            with pytest.raises(ValueError, match="Failed to parse response"):
                extract_facts(sample_raw_text)


class TestAuditorPrompt:
    """Tests for prompt construction and security."""
    
    def test_prompt_uses_xml_delimiters(self, sample_raw_text, mock_auditor_response):
        """Verify the prompt uses XML delimiters for injection protection."""
        with patch('core.auditor.get_gemini_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_auditor_response
            mock_get_client.return_value = mock_client
            
            extract_facts(sample_raw_text)
            
            call_args = mock_client.models.generate_content.call_args
            prompt = call_args.kwargs.get('contents', '')
            
            # Check for XML delimiters
            assert "<USER_INPUT>" in prompt
            assert "</USER_INPUT>" in prompt
    
    def test_prompt_contains_raw_text(self, sample_raw_text, mock_auditor_response):
        """Verify the user's raw text is included in the prompt."""
        with patch('core.auditor.get_gemini_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_auditor_response
            mock_get_client.return_value = mock_client
            
            extract_facts(sample_raw_text)
            
            call_args = mock_client.models.generate_content.call_args
            prompt = call_args.kwargs.get('contents', '')
            
            # The raw text should be in the prompt
            assert "Machine Learning" in prompt or "15th January" in prompt
