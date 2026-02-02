"""
Template Storage Module - Persistent Event Templates.

Provides functions to save, load, and manage reusable event templates.
Templates are stored as JSON files in the templates/ directory.
"""
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

from models.schemas import EventTemplate, EventFacts


# Templates directory path (relative to project root)
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


def _ensure_templates_dir():
    """Create templates directory if it doesn't exist."""
    TEMPLATES_DIR.mkdir(exist_ok=True)


def _get_template_path(template_id: str) -> Path:
    """Get the file path for a template by ID."""
    return TEMPLATES_DIR / f"{template_id}.json"


def save_template(template: EventTemplate) -> bool:
    """
    Save a template to disk.
    
    Args:
        template: The EventTemplate to save
        
    Returns:
        True if saved successfully
    """
    _ensure_templates_dir()
    
    # Update timestamp if not set
    if not template.created_at:
        template.created_at = datetime.now().isoformat()
    
    path = _get_template_path(template.id)
    path.write_text(template.model_dump_json(indent=2))
    return True


def load_templates() -> List[EventTemplate]:
    """
    Load all templates from disk.
    
    Returns:
        List of EventTemplate objects, sorted by use_count (most used first)
    """
    _ensure_templates_dir()
    
    templates = []
    for file in TEMPLATES_DIR.glob("*.json"):
        try:
            data = json.loads(file.read_text())
            templates.append(EventTemplate(**data))
        except json.JSONDecodeError as e:
            logger.warning(f"Skipping corrupt template {file.name}: JSON decode error - {e}")
            continue
        except Exception as e:
            logger.warning(f"Skipping invalid template {file.name}: {e}")
            continue
    
    # Sort by use count (most popular first)
    return sorted(templates, key=lambda t: t.use_count, reverse=True)


def get_template(template_id: str) -> Optional[EventTemplate]:
    """
    Get a specific template by ID.
    
    Args:
        template_id: The unique template identifier
        
    Returns:
        EventTemplate if found, None otherwise
    """
    path = _get_template_path(template_id)
    
    if not path.exists():
        return None
    
    try:
        data = json.loads(path.read_text())
        return EventTemplate(**data)
    except (json.JSONDecodeError, Exception):
        return None


def increment_use_count(template_id: str) -> bool:
    """
    Increment the use count for a template.
    
    Args:
        template_id: The template ID to update
        
    Returns:
        True if updated successfully
    """
    template = get_template(template_id)
    if template:
        template.use_count += 1
        save_template(template)
        return True
    return False


def delete_template(template_id: str) -> bool:
    """
    Delete a template by ID.
    
    Args:
        template_id: The template ID to delete
        
    Returns:
        True if deleted successfully
    """
    path = _get_template_path(template_id)
    if path.exists():
        path.unlink()
        return True
    return False


def apply_template(template: EventTemplate) -> EventFacts:
    """
    Create an EventFacts instance with template defaults applied.
    
    Args:
        template: The template to apply
        
    Returns:
        EventFacts with template defaults pre-filled
    """
    return EventFacts(
        organizer=template.default_organizer,
        mode=template.default_mode,
        target_audience=template.default_target_audience,
        agenda=template.suggested_agenda,
    )


def create_template_from_facts(
    facts: EventFacts, 
    name: str,
    template_id: str,
    description: str = "",
    category: str = "Custom"
) -> EventTemplate:
    """
    Create a new template from existing EventFacts.
    
    Args:
        facts: The EventFacts to use as a base
        name: Human-readable template name
        template_id: Unique template ID (slug)
        description: Brief description
        category: Category for grouping
        
    Returns:
        The created EventTemplate
    """
    return EventTemplate(
        id=template_id,
        name=name,
        description=description,
        category=category,
        default_organizer=facts.organizer or "IEEE RIT Student Branch",
        default_mode=facts.mode,
        default_target_audience=facts.target_audience,
        suggested_agenda=facts.agenda,
        created_at=datetime.now().isoformat(),
        use_count=0,
    )


# --- BUILT-IN TEMPLATES ---

def get_builtin_templates() -> List[EventTemplate]:
    """
    Return a list of built-in templates for common event types.
    These are always available even if no custom templates exist.
    """
    return [
        EventTemplate(
            id="workshop",
            name="🛠️ Technical Workshop",
            description="Hands-on learning session with a speaker/instructor",
            category="Technical",
            default_organizer="IEEE RIT Student Branch",
            default_mode="Offline",
            default_target_audience="Engineering Students",
            suggested_agenda="Registration → Welcome → Session 1 → Break → Session 2 → Q&A → Feedback",
        ),
        EventTemplate(
            id="hackathon",
            name="💻 Hackathon",
            description="Competitive coding/building event with teams and prizes",
            category="Competition",
            default_organizer="IEEE RIT Student Branch",
            default_mode="Hybrid",
            default_target_audience="All Engineering Students",
            suggested_agenda="Inauguration → Problem Statement → Hacking Phase → Judging → Prize Distribution",
        ),
        EventTemplate(
            id="seminar",
            name="🎓 Guest Seminar",
            description="Talk or lecture by an industry/academic expert",
            category="Knowledge",
            default_organizer="IEEE RIT Student Branch",
            default_mode="Offline",
            default_target_audience="Faculty and Students",
            suggested_agenda="Welcome → Introduction → Keynote → Q&A → Vote of Thanks",
        ),
        EventTemplate(
            id="webinar",
            name="🌐 Online Webinar",
            description="Virtual session delivered online",
            category="Technical",
            default_organizer="IEEE RIT Student Branch",
            default_mode="Online",
            default_target_audience="All IEEE Members",
            suggested_agenda="Zoom Link → Introduction → Presentation → Live Q&A → Closing",
        ),
        EventTemplate(
            id="competition",
            name="🏆 Technical Competition",
            description="Contest with multiple rounds and winners",
            category="Competition",
            default_organizer="IEEE RIT Student Branch",
            default_mode="Offline",
            default_target_audience="Engineering Students",
            suggested_agenda="Registration → Round 1 → Round 2 → Finals → Results → Prize Ceremony",
        ),
    ]
