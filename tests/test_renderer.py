"""
Unit tests for the Renderer (DOCX Generation) module.
Tests cover: DOCX creation, Jinja sanitization, and None value handling.
"""
import pytest
from io import BytesIO
from unittest.mock import patch, Mock

from core.renderer import render_report, sanitize_jinja_input, sanitize_view_model
from models.schemas import EventFacts, EventNarrative, FullReport


class TestJinjaSanitization:
    """Tests for Jinja2 injection prevention."""
    
    def test_sanitize_double_braces(self):
        """Test that {{ }} are escaped to prevent template injection."""
        malicious = "Hello {{ dangerous_code }}"
        result = sanitize_jinja_input(malicious)
        
        assert "{{" not in result
        assert "{ {" in result
    
    def test_sanitize_closing_braces(self):
        """Test that }} are also escaped."""
        malicious = "Code: {{ x }}"
        result = sanitize_jinja_input(malicious)
        
        assert "}}" not in result
        assert "} }" in result
    
    def test_sanitize_jinja_tags(self):
        """Test that {% %} tags are escaped."""
        malicious = "{% for i in items %}"
        result = sanitize_jinja_input(malicious)
        
        assert "{%" not in result
        assert "{ %" in result
    
    def test_sanitize_closing_tags(self):
        """Test that %} is escaped."""
        malicious = "{% if x %}"
        result = sanitize_jinja_input(malicious)
        
        assert "%}" not in result
        assert "% }" in result
    
    def test_sanitize_non_string_passthrough(self):
        """Test that non-strings pass through unchanged."""
        assert sanitize_jinja_input(123) == 123
        assert sanitize_jinja_input(None) is None
        assert sanitize_jinja_input([1, 2, 3]) == [1, 2, 3]
    
    def test_sanitize_clean_string_unchanged(self):
        """Test that clean strings without Jinja are unchanged."""
        clean = "This is a normal event description."
        result = sanitize_jinja_input(clean)
        
        assert result == clean


class TestSanitizeViewModel:
    """Tests for the full view model sanitization."""
    
    def test_none_values_replaced_with_na(self, sample_full_report):
        """Test that None values in facts become 'N/A'."""
        report = FullReport(
            facts=EventFacts(
                event_title="Test",
                venue=None,
                speaker_name=None
            ),
            narrative=EventNarrative(
                executive_summary="Test summary",
                key_takeaways=["Point 1"]
            ),
            confidence_score=0.9
        )
        
        result = sanitize_view_model(report)
        
        assert result["facts"]["venue"] == "N/A"
        assert result["facts"]["speaker_name"] == "N/A"
    
    def test_empty_takeaways_get_default(self, sample_event_facts):
        """Test that empty key_takeaways gets a default message."""
        report = FullReport(
            facts=sample_event_facts,
            narrative=EventNarrative(
                executive_summary="Summary",
                key_takeaways=[]
            ),
            confidence_score=0.9
        )
        
        result = sanitize_view_model(report)
        
        assert len(result["key_takeaways"]) == 1
        assert "No specific takeaways" in result["key_takeaways"][0]
    
    def test_list_fields_preserved_if_empty(self, sample_event_facts):
        """Test that empty list fields remain as empty lists."""
        sample_event_facts.judges = []
        sample_event_facts.student_coordinators = []
        
        report = FullReport(
            facts=sample_event_facts,
            narrative=EventNarrative(
                executive_summary="Summary",
                key_takeaways=["Point"]
            ),
            confidence_score=0.9
        )
        
        result = sanitize_view_model(report)
        
        assert result["facts"]["judges"] == []
        assert result["facts"]["student_coordinators"] == []
    
    def test_takeaways_are_sanitized(self):
        """Test that key_takeaways are also sanitized for Jinja."""
        report = FullReport(
            facts=EventFacts(event_title="Test"),
            narrative=EventNarrative(
                executive_summary="Summary",
                key_takeaways=["Normal point", "Malicious {{ code }}"]
            ),
            confidence_score=0.9
        )
        
        result = sanitize_view_model(report)
        
        assert "{{" not in result["key_takeaways"][1]


class TestRenderReport:
    """Tests for the main render_report function."""
    
    def test_render_returns_bytesio(self, sample_full_report):
        """Test that rendering returns a BytesIO stream."""
        with patch('core.renderer.DocxTemplate') as mock_docx:
            mock_doc = Mock()
            mock_docx.return_value = mock_doc
            
            result = render_report(sample_full_report)
            
            assert isinstance(result, BytesIO)
    
    def test_render_calls_template(self, sample_full_report):
        """Test that the template is loaded and rendered."""
        with patch('core.renderer.DocxTemplate') as mock_docx:
            mock_doc = Mock()
            mock_docx.return_value = mock_doc
            
            render_report(sample_full_report, template_path="test_template.docx")
            
            mock_docx.assert_called_once_with("test_template.docx")
            mock_doc.render.assert_called_once()
    
    def test_render_saves_to_stream(self, sample_full_report):
        """Test that the document is saved to the BytesIO stream."""
        with patch('core.renderer.DocxTemplate') as mock_docx:
            mock_doc = Mock()
            mock_docx.return_value = mock_doc
            
            result = render_report(sample_full_report)
            
            mock_doc.save.assert_called_once()
            # Stream should be seeked to start
            assert result.tell() == 0
    
    def test_render_context_structure(self, sample_full_report):
        """Test that the context passed to template has expected keys."""
        with patch('core.renderer.DocxTemplate') as mock_docx:
            mock_doc = Mock()
            mock_docx.return_value = mock_doc
            
            render_report(sample_full_report)
            
            render_call = mock_doc.render.call_args
            context = render_call[0][0]
            
            assert "facts" in context
            assert "narrative" in context
            assert "executive_summary" in context
            assert "key_takeaways" in context
