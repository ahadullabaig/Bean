"""
Unit tests for the Auditor (Fact Extraction) module.
Tests cover: valid extraction, empty input, and malformed responses.
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
    
    def test_extract_facts_handles_none_parsed_response(self, sample_raw_text):
        """
        Test behavior when response.parsed is None.
        NOTE: This test documents current behavior. 
        In Phase 2, we'll add a validation fallback.
        """
        with patch('core.auditor.get_gemini_client') as mock_get_client:
            mock_response = Mock()
            mock_response.parsed = None  # Simulates malformed JSON
            mock_response.text = "invalid json {"
            
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_response
            mock_get_client.return_value = mock_client
            
            # Currently this will return None - Phase 2 will fix this
            result = extract_facts(sample_raw_text)
            
            # Document current (broken) behavior
            assert result is None


class TestAuditorPrompt:
    """Tests for prompt construction."""
    
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
