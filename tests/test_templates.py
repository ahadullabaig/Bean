"""
Unit tests for the Templates module.
Tests cover: CRUD operations, built-in templates, and error handling.
"""
import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from core.templates import (
    load_templates, save_template, get_template, 
    delete_template, increment_use_count, get_builtin_templates,
    create_template_from_facts, apply_template, TEMPLATES_DIR
)
from models.schemas import EventTemplate, EventFacts


class TestBuiltinTemplates:
    """Tests for built-in template functionality."""
    
    def test_get_builtin_templates_returns_list(self):
        """Test that built-in templates return a non-empty list."""
        templates = get_builtin_templates()
        assert isinstance(templates, list)
        assert len(templates) == 5  # Workshop, Hackathon, Seminar, Webinar, Competition
    
    def test_builtin_templates_have_required_fields(self):
        """Test that all built-in templates have required fields."""
        templates = get_builtin_templates()
        for template in templates:
            assert template.id is not None
            assert template.name is not None
            assert template.default_organizer == "IEEE RIT Student Branch"
    
    def test_builtin_template_ids_are_unique(self):
        """Test that all built-in template IDs are unique."""
        templates = get_builtin_templates()
        ids = [t.id for t in templates]
        assert len(ids) == len(set(ids))


class TestTemplateCRUD:
    """Tests for template Create, Read, Update, Delete operations."""
    
    @pytest.fixture
    def temp_templates_dir(self, tmp_path):
        """Create a temporary templates directory for testing."""
        with patch('core.templates.TEMPLATES_DIR', tmp_path):
            yield tmp_path
    
    @pytest.fixture
    def sample_template(self):
        """Create a sample template for testing."""
        return EventTemplate(
            id="test-template",
            name="Test Template",
            description="A test template",
            category="Test",
            default_organizer="Test Org",
            default_mode="Offline"
        )
    
    def test_save_and_load_template(self, temp_templates_dir, sample_template):
        """Test saving and loading a template."""
        with patch('core.templates.TEMPLATES_DIR', temp_templates_dir):
            # Save
            result = save_template(sample_template)
            assert result is True
            
            # Verify file exists
            template_file = temp_templates_dir / f"{sample_template.id}.json"
            assert template_file.exists()
            
            # Load
            templates = load_templates()
            assert len(templates) == 1
            assert templates[0].id == sample_template.id
            assert templates[0].name == sample_template.name
    
    def test_get_template_by_id(self, temp_templates_dir, sample_template):
        """Test retrieving a specific template by ID."""
        with patch('core.templates.TEMPLATES_DIR', temp_templates_dir):
            save_template(sample_template)
            
            # Get existing template
            template = get_template(sample_template.id)
            assert template is not None
            assert template.id == sample_template.id
            
            # Get non-existent template
            missing = get_template("non-existent-id")
            assert missing is None
    
    def test_delete_template(self, temp_templates_dir, sample_template):
        """Test deleting a template."""
        with patch('core.templates.TEMPLATES_DIR', temp_templates_dir):
            save_template(sample_template)
            
            # Delete existing
            result = delete_template(sample_template.id)
            assert result is True
            
            # Verify deleted
            template = get_template(sample_template.id)
            assert template is None
            
            # Delete non-existent
            result = delete_template("non-existent-id")
            assert result is False
    
    def test_increment_use_count(self, temp_templates_dir, sample_template):
        """Test incrementing template use count."""
        with patch('core.templates.TEMPLATES_DIR', temp_templates_dir):
            save_template(sample_template)
            
            # Increment
            result = increment_use_count(sample_template.id)
            assert result is True
            
            # Verify count increased
            template = get_template(sample_template.id)
            assert template.use_count == 1
            
            # Increment non-existent
            result = increment_use_count("non-existent-id")
            assert result is False


class TestTemplateFactory:
    """Tests for template creation and application."""
    
    def test_create_template_from_facts(self):
        """Test creating a template from EventFacts."""
        facts = EventFacts(
            organizer="Test Org",
            mode="Online",
            target_audience="Students",
            agenda="Test agenda"
        )
        
        template = create_template_from_facts(
            facts=facts,
            name="My Template",
            template_id="my-template",
            description="Test description",
            category="Custom"
        )
        
        assert template.id == "my-template"
        assert template.name == "My Template"
        assert template.default_organizer == "Test Org"
        assert template.default_mode == "Online"
        assert template.default_target_audience == "Students"
        assert template.suggested_agenda == "Test agenda"
    
    def test_apply_template(self):
        """Test applying a template to create EventFacts."""
        template = EventTemplate(
            id="test",
            name="Test",
            default_organizer="Applied Org",
            default_mode="Hybrid",
            default_target_audience="Faculty",
            suggested_agenda="Applied agenda"
        )
        
        facts = apply_template(template)
        
        assert facts.organizer == "Applied Org"
        assert facts.mode == "Hybrid"
        assert facts.target_audience == "Faculty"
        assert facts.agenda == "Applied agenda"


class TestTemplateErrorHandling:
    """Tests for error handling in template operations."""
    
    def test_load_templates_skips_corrupt_json(self, tmp_path):
        """Test that corrupt JSON files are skipped with warning."""
        with patch('core.templates.TEMPLATES_DIR', tmp_path):
            # Create corrupt JSON file
            (tmp_path / "corrupt.json").write_text("{ invalid json }")
            
            # Should not raise, should return empty list
            templates = load_templates()
            assert templates == []
    
    def test_load_templates_skips_invalid_schema(self, tmp_path):
        """Test that valid JSON with invalid schema is skipped."""
        with patch('core.templates.TEMPLATES_DIR', tmp_path):
            # Create valid JSON but invalid template schema (missing required id)
            (tmp_path / "invalid.json").write_text('{"name": "Missing ID"}')
            
            templates = load_templates()
            assert templates == []
