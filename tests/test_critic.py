"""
Unit tests for the Critic (Hallucination Checker) module.
Tests cover: safe verdicts, detected issues, confidence scoring, and edge cases.
"""
import pytest
from unittest.mock import patch, Mock, MagicMock

from core.critic import check_consistency
from models.schemas import CriticVerdict


class TestCriticConsistencyCheck:
    """Tests for the check_consistency function."""
    
    @pytest.fixture
    def mock_safe_verdict(self):
        """Mock response for a safe verdict."""
        return CriticVerdict(
            is_safe=True,
            confidence=0.95,
            issues=[],
            reasoning="All facts in the report are supported by the source text."
        )
    
    @pytest.fixture
    def mock_unsafe_verdict(self):
        """Mock response for an unsafe verdict with issues."""
        return CriticVerdict(
            is_safe=False,
            confidence=0.85,
            issues=[
                "Report mentions 50 attendees but source says 45",
                "Speaker title 'Professor' not mentioned in source"
            ],
            reasoning="Found 2 facts in the report not supported by source."
        )
    
    def test_check_consistency_safe_report(self, sample_raw_text, mock_safe_verdict):
        """Test that a consistent report returns safe verdict."""
        with patch('core.critic.get_gemini_client') as mock_get_client:
            mock_response = Mock()
            mock_response.parsed = mock_safe_verdict
            
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_response
            mock_get_client.return_value = mock_client
            
            report_text = "Workshop on Machine Learning was conducted on 15th January 2024."
            result = check_consistency(sample_raw_text, report_text)
            
            assert isinstance(result, CriticVerdict)
            assert result.is_safe is True
            assert result.confidence > 0.8
            assert len(result.issues) == 0
    
    def test_check_consistency_finds_hallucinations(self, sample_raw_text, mock_unsafe_verdict):
        """Test that hallucinated facts are detected and returned."""
        with patch('core.critic.get_gemini_client') as mock_get_client:
            mock_response = Mock()
            mock_response.parsed = mock_unsafe_verdict
            
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_response
            mock_get_client.return_value = mock_client
            
            report_text = "The workshop had 50 attendees. Professor Sharma presented."
            result = check_consistency(sample_raw_text, report_text)
            
            assert isinstance(result, CriticVerdict)
            assert result.is_safe is False
            assert len(result.issues) == 2
            assert any("50" in issue for issue in result.issues)
    
    def test_check_consistency_returns_confidence(self, sample_raw_text, mock_safe_verdict):
        """Test that confidence score is included in verdict."""
        with patch('core.critic.get_gemini_client') as mock_get_client:
            mock_response = Mock()
            mock_response.parsed = mock_safe_verdict
            
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_response
            mock_get_client.return_value = mock_client
            
            result = check_consistency(sample_raw_text, "Some report")
            
            assert hasattr(result, 'confidence')
            assert 0.0 <= result.confidence <= 1.0
    
    def test_check_consistency_returns_reasoning(self, sample_raw_text, mock_safe_verdict):
        """Test that reasoning is included in verdict."""
        with patch('core.critic.get_gemini_client') as mock_get_client:
            mock_response = Mock()
            mock_response.parsed = mock_safe_verdict
            
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_response
            mock_get_client.return_value = mock_client
            
            result = check_consistency(sample_raw_text, "Some report")
            
            assert hasattr(result, 'reasoning')
            assert len(result.reasoning) > 0


class TestCriticFallback:
    """Tests for fallback behavior when parsing fails."""
    
    def test_fallback_on_parse_failure(self, sample_raw_text):
        """Test that a default safe verdict is returned when all retries fail."""
        with patch('core.critic.get_gemini_client') as mock_get_client:
            mock_response = Mock()
            mock_response.parsed = None
            mock_response.text = "invalid json {"
            
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_response
            mock_get_client.return_value = mock_client
            
            result = check_consistency(sample_raw_text, "Some report")
            
            # Should return a low-confidence safe verdict
            assert isinstance(result, CriticVerdict)
            assert result.is_safe is True
            assert result.confidence < 0.5  # Low confidence indicates uncertainty


class TestCriticPrompt:
    """Tests for prompt construction."""
    
    def test_prompt_uses_xml_delimiters(self, sample_raw_text):
        """Verify the prompt uses XML delimiters for injection protection."""
        with patch('core.critic.get_gemini_client') as mock_get_client:
            mock_response = Mock()
            mock_response.parsed = CriticVerdict(
                is_safe=True, confidence=0.9, issues=[], reasoning="OK"
            )
            
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_response
            mock_get_client.return_value = mock_client
            
            check_consistency(sample_raw_text, "report text")
            
            call_args = mock_client.models.generate_content.call_args
            prompt = str(call_args.kwargs.get('contents', ''))
            
            # Check for XML delimiters
            assert "<SOURCE_TEXT>" in prompt
            assert "</SOURCE_TEXT>" in prompt
            assert "<GENERATED_REPORT>" in prompt
    
    def test_calls_with_temperature_zero(self, sample_raw_text):
        """Verify critic uses temperature 0.0 for deterministic output."""
        with patch('core.critic.get_gemini_client') as mock_get_client:
            mock_response = Mock()
            mock_response.parsed = CriticVerdict(
                is_safe=True, confidence=0.9, issues=[], reasoning="OK"
            )
            
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_response
            mock_get_client.return_value = mock_client
            
            check_consistency(sample_raw_text, "report")
            
            call_args = mock_client.models.generate_content.call_args
            config = call_args.kwargs.get('config', {})
            
            assert config.get('temperature') == 0.0
