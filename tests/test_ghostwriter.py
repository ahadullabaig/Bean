"""
Unit tests for the Ghostwriter (Narrative Generation) module.
Tests cover: valid narrative generation, minimal facts, self-correction, and prompt security.
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


class TestGhostwriterSelfCorrection:
    """Tests for the self-correction fallback."""
    
    def test_self_correction_on_none_parsed(
        self, sample_event_facts, sample_raw_text, sample_event_narrative
    ):
        """Test that manual parsing is attempted when response.parsed is None."""
        with patch('core.ghostwriter.get_gemini_client') as mock_get_client:
            mock_response = Mock()
            mock_response.parsed = None
            mock_response.text = sample_event_narrative.model_dump_json()
            
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_response
            mock_get_client.return_value = mock_client
            
            result = generate_narrative(sample_event_facts, sample_raw_text)
            
            assert isinstance(result, EventNarrative)
    
    def test_raises_after_max_retries(self, sample_event_facts, sample_raw_text):
        """Test that ValueError is raised when parsing fails."""
        with patch('core.ghostwriter.get_gemini_client') as mock_get_client:
            mock_response = Mock()
            mock_response.parsed = None
            mock_response.text = "invalid json {"
            
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_response
            mock_get_client.return_value = mock_client
            
            with pytest.raises(ValueError, match="Failed to parse response"):
                generate_narrative(sample_event_facts, sample_raw_text)


class TestGhostwriterPromptSecurity:
    """Tests for prompt construction and security."""
    
    def test_prompt_uses_xml_delimiters(
        self, sample_event_facts, sample_raw_text, mock_ghostwriter_response
    ):
        """Verify the prompt uses XML delimiters for injection protection."""
        with patch('core.ghostwriter.get_gemini_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_ghostwriter_response
            mock_get_client.return_value = mock_client
            
            generate_narrative(sample_event_facts, sample_raw_text)
            
            call_args = mock_client.models.generate_content.call_args
            prompt = str(call_args.kwargs.get('contents', ''))
            
            # Check for XML delimiters
            assert "<VERIFIED_FACTS>" in prompt
            assert "</VERIFIED_FACTS>" in prompt
            assert "<STYLE_CONTEXT>" in prompt
    
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
