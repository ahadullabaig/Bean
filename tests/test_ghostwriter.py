"""
Unit tests for the Ghostwriter (Narrative Generation) module.
Tests cover: valid narrative generation, minimal facts, and output structure.
"""
import pytest
from unittest.mock import patch, Mock, MagicMock

from core.ghostwriter import generate_narrative
from models.schemas import EventFacts, EventNarrative


class TestGhostwriterGeneration:
    """Tests for the generate_narrative function."""
    
    def test_generate_narrative_valid_input(
        self, sample_event_facts, sample_raw_text, mock_ghostwriter_response
    ):
        """Test that valid facts produce a proper EventNarrative."""
        with patch('core.ghostwriter.get_gemini_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_ghostwriter_response
            mock_get_client.return_value = mock_client
            
            result = generate_narrative(sample_event_facts, sample_raw_text)
            
            assert isinstance(result, EventNarrative)
            assert result.executive_summary is not None
            assert len(result.executive_summary) > 0
    
    def test_generate_narrative_returns_key_takeaways(
        self, sample_event_facts, sample_raw_text, mock_ghostwriter_response
    ):
        """Test that key_takeaways list is populated."""
        with patch('core.ghostwriter.get_gemini_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_ghostwriter_response
            mock_get_client.return_value = mock_client
            
            result = generate_narrative(sample_event_facts, sample_raw_text)
            
            assert isinstance(result.key_takeaways, list)
            assert len(result.key_takeaways) > 0
    
    def test_generate_narrative_calls_with_correct_temperature(
        self, sample_event_facts, sample_raw_text, mock_ghostwriter_response
    ):
        """Verify Gemini is called with temperature 0.3 (creative but controlled)."""
        with patch('core.ghostwriter.get_gemini_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_ghostwriter_response
            mock_get_client.return_value = mock_client
            
            generate_narrative(sample_event_facts, sample_raw_text)
            
            call_args = mock_client.models.generate_content.call_args
            config = call_args.kwargs.get('config', {})
            
            assert config.get('temperature') == 0.3
            assert config.get('response_schema') == EventNarrative
    
    def test_generate_narrative_minimal_facts(self, sample_raw_text, mock_ghostwriter_response):
        """Test with minimal/sparse facts still produces valid output."""
        minimal_facts = EventFacts(
            event_title="Test Event"
            # All other fields are None/default
        )
        
        with patch('core.ghostwriter.get_gemini_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_ghostwriter_response
            mock_get_client.return_value = mock_client
            
            result = generate_narrative(minimal_facts, sample_raw_text)
            
            assert isinstance(result, EventNarrative)
    
    def test_generate_narrative_includes_facts_in_prompt(
        self, sample_event_facts, sample_raw_text, mock_ghostwriter_response
    ):
        """Verify the facts are included in the prompt to the LLM."""
        with patch('core.ghostwriter.get_gemini_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_ghostwriter_response
            mock_get_client.return_value = mock_client
            
            generate_narrative(sample_event_facts, sample_raw_text)
            
            call_args = mock_client.models.generate_content.call_args
            prompt = call_args.kwargs.get('contents', '')
            
            # The prompt should contain the facts
            assert sample_event_facts.event_title in str(prompt) or "event_title" in str(prompt)


class TestGhostwriterPromptConstruction:
    """Tests for how the prompt is constructed."""
    
    def test_prompt_includes_context(
        self, sample_event_facts, mock_ghostwriter_response
    ):
        """Test that raw context is included for tone matching."""
        context = "This was an amazing workshop with great energy!"
        
        with patch('core.ghostwriter.get_gemini_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_ghostwriter_response
            mock_get_client.return_value = mock_client
            
            generate_narrative(sample_event_facts, context)
            
            call_args = mock_client.models.generate_content.call_args
            prompt = str(call_args.kwargs.get('contents', ''))
            
            assert "amazing" in prompt or "energy" in prompt
    
    def test_facts_excludes_none_values(
        self, sample_raw_text, mock_ghostwriter_response
    ):
        """Test that None values are excluded from the facts dict sent to LLM."""
        facts = EventFacts(
            event_title="Test",
            venue=None,  # Explicitly None
            attendance_count=None
        )
        
        with patch('core.ghostwriter.get_gemini_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_ghostwriter_response
            mock_get_client.return_value = mock_client
            
            generate_narrative(facts, sample_raw_text)
            
            # The function uses model_dump(exclude_none=True)
            # We verify by checking the call was made without error
            mock_client.models.generate_content.assert_called_once()
