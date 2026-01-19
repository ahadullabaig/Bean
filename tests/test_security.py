"""Tests for Jinja2 template injection prevention in renderer."""
import pytest
from core.renderer import sanitize_jinja_input, sanitize_view_model
from models.schemas import EventFacts, EventNarrative, FullReport


class TestJinjaSanitization:
    """Tests for Jinja2 template injection prevention."""
    
    def test_sanitize_double_braces_opening(self):
        """Test that {{ is escaped."""
        malicious = "Hello {{ config }}"
        result = sanitize_jinja_input(malicious)
        assert "{{" not in result
        assert "{ {" in result
    
    def test_sanitize_double_braces_closing(self):
        """Test that }} is escaped."""
        malicious = "{{ config }}"
        result = sanitize_jinja_input(malicious)
        assert "}}" not in result
        assert "} }" in result
    
    def test_sanitize_block_tags(self):
        """Test that {% %} are escaped."""
        malicious = "{% for x in y %}loop{% endfor %}"
        result = sanitize_jinja_input(malicious)
        assert "{%" not in result
        assert "%}" not in result
        assert "{ %" in result
        assert "% }" in result
    
    def test_sanitize_preserves_normal_text(self):
        """Test that normal text is unchanged."""
        normal = "This is a normal event report with {curly} braces."
        result = sanitize_jinja_input(normal)
        assert result == normal
    
    def test_sanitize_non_string_passthrough(self):
        """Test that non-string values pass through unchanged."""
        assert sanitize_jinja_input(42) == 42
        assert sanitize_jinja_input(None) is None
        assert sanitize_jinja_input(3.14) == 3.14
    
    def test_sanitize_view_model_escapes_facts(self):
        """Test that malicious facts are sanitized in view model."""
        facts = EventFacts(
            event_title="{{ config.items() }}",
            date="2026-01-19",
            venue="{% include 'evil' %}"
        )
        narrative = EventNarrative(
            executive_summary="Normal summary",
            key_takeaways=["{{ secret }}"]
        )
        report = FullReport(
            facts=facts,
            narrative=narrative,
            confidence_score=1.0
        )
        
        result = sanitize_view_model(report)
        
        # Check facts are sanitized
        assert "{{" not in result["facts"]["event_title"]
        assert "{%" not in result["facts"]["venue"]
        # Check takeaways are sanitized  
        assert "{{" not in result["key_takeaways"][0]
    
    def test_sanitize_view_model_handles_none(self):
        """Test that None values become N/A."""
        facts = EventFacts(event_title=None, date=None)
        narrative = EventNarrative(
            executive_summary="Summary",
            key_takeaways=[]
        )
        report = FullReport(
            facts=facts,
            narrative=narrative,
            confidence_score=1.0
        )
        
        result = sanitize_view_model(report)
        
        assert result["facts"]["event_title"] == "N/A"
        assert result["facts"]["date"] == "N/A"
        assert len(result["key_takeaways"]) == 1  # Placeholder added
