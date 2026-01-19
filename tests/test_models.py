import json
import pytest
from models.schemas import EventFacts, EventNarrative, FullReport

def test_constants_json_validity():
    """Ensure constants.json is valid JSON and has expected keys."""
    with open("utils/constants.json", "r") as f:
        data = json.load(f)
    assert "organization_name" in data
    assert "branch_counselor" in data
    assert "standard_venues" in data
    assert isinstance(data["standard_venues"], list)

def test_event_facts_model():
    """Test EventFacts validation."""
    # Test valid data
    facts = EventFacts(
        event_title="AI Workshop",
        date="2023-10-25",
        attendance_count=50
    )
    assert facts.event_title == "AI Workshop"
    assert facts.attendance_count == 50
    assert facts.speaker_name is None  # Optional field

    # Test invalid type (should coerce if possible, or fail)
    # Pydantic attempts coercion, so "50" becomes 50.
    facts_coerced = EventFacts(attendance_count="50")
    assert facts_coerced.attendance_count == 50

def test_full_report_structure():
    """Test the nesting of the FullReport model."""
    facts = EventFacts(event_title="Hackathon")
    narrative = EventNarrative(
        executive_summary="It was great.",
        key_takeaways=["Fun", "Learned a lot"]
    )
    report = FullReport(
        facts=facts,
        narrative=narrative,
        confidence_score=0.95
    )
    assert report.confidence_score == 0.95
    assert report.facts.event_title == "Hackathon"
    assert len(report.narrative.key_takeaways) == 2
