"""
Unit tests for the Critic (Hallucination Checker) module.
Tests cover: safe reports, detected issues, and edge cases.
"""
import pytest
from unittest.mock import patch, Mock, MagicMock

from core.critic import check_consistency


class TestCriticConsistencyCheck:
    """Tests for the check_consistency function."""
    
    def test_check_consistency_safe_report(self, sample_raw_text, mock_critic_safe_response):
        """Test that a consistent report returns empty list (no issues)."""
        with patch('core.critic.get_gemini_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_critic_safe_response
            mock_get_client.return_value = mock_client
            
            report_text = "Workshop on Machine Learning was conducted on 15th January 2024."
            result = check_consistency(sample_raw_text, report_text)
            
            assert isinstance(result, list)
            assert len(result) == 0
    
    def test_check_consistency_finds_hallucinations(self, sample_raw_text, mock_critic_issues_response):
        """Test that hallucinated facts are detected and returned."""
        with patch('core.critic.get_gemini_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_critic_issues_response
            mock_get_client.return_value = mock_client
            
            # Report with invented facts
            report_text = "The workshop had 50 attendees. Professor Sharma presented."
            result = check_consistency(sample_raw_text, report_text)
            
            assert isinstance(result, list)
            assert len(result) > 0
            # Check that specific issues are captured
            assert any("50" in issue or "attendees" in issue.lower() for issue in result)
    
    def test_check_consistency_empty_source(self):
        """Test behavior when source text is empty."""
        with patch('core.critic.get_gemini_client') as mock_get_client:
            mock_response = Mock()
            mock_response.text = "SAFE"
            
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_response
            mock_get_client.return_value = mock_client
            
            result = check_consistency("", "Some report text")
            
            # Should still function and return a list
            assert isinstance(result, list)
    
    def test_check_consistency_empty_report(self, sample_raw_text):
        """Test behavior when report text is empty."""
        with patch('core.critic.get_gemini_client') as mock_get_client:
            mock_response = Mock()
            mock_response.text = "SAFE"
            
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_response
            mock_get_client.return_value = mock_client
            
            result = check_consistency(sample_raw_text, "")
            
            assert isinstance(result, list)
    
    def test_check_consistency_no_response_text(self, sample_raw_text):
        """Test when LLM returns None/empty response."""
        with patch('core.critic.get_gemini_client') as mock_get_client:
            mock_response = Mock()
            mock_response.text = None
            
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_response
            mock_get_client.return_value = mock_client
            
            result = check_consistency(sample_raw_text, "Some report")
            
            # Should return empty list, not crash
            assert result == []


class TestCriticOutputParsing:
    """Tests for parsing the Critic's text output."""
    
    def test_parses_bullet_points(self, sample_raw_text):
        """Test that bullet-pointed issues are correctly parsed."""
        with patch('core.critic.get_gemini_client') as mock_get_client:
            mock_response = Mock()
            mock_response.text = """
            - Issue one about dates
            - Issue two about names
            - Issue three about numbers
            """
            
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_response
            mock_get_client.return_value = mock_client
            
            result = check_consistency(sample_raw_text, "report")
            
            assert len(result) == 3
            assert "Issue one" in result[0]
    
    def test_parses_asterisk_bullets(self, sample_raw_text):
        """Test that asterisk-style bullets are also parsed."""
        with patch('core.critic.get_gemini_client') as mock_get_client:
            mock_response = Mock()
            mock_response.text = """
            * First issue
            * Second issue
            """
            
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_response
            mock_get_client.return_value = mock_client
            
            result = check_consistency(sample_raw_text, "report")
            
            assert len(result) == 2
    
    def test_safe_variations(self, sample_raw_text):
        """Test that various forms of 'SAFE' response are handled."""
        safe_variations = [
            "SAFE",
            "SAFE.",
            "The report is SAFE.",
            "SAFE - no issues found"
        ]
        
        for safe_text in safe_variations:
            with patch('core.critic.get_gemini_client') as mock_get_client:
                mock_response = Mock()
                mock_response.text = safe_text
                
                mock_client = MagicMock()
                mock_client.models.generate_content.return_value = mock_response
                mock_get_client.return_value = mock_client
                
                result = check_consistency(sample_raw_text, "report")
                
                assert result == [], f"Failed for: {safe_text}"
