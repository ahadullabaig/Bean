"""
Pytest fixtures for Bean unit tests.
Provides mocked Gemini client and sample data to avoid hitting real API.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from models.schemas import EventFacts, EventNarrative, FullReport, Winner


# --- Sample Data Fixtures ---

@pytest.fixture
def sample_raw_text():
    """Raw event notes as a user might input."""
    return """
    We conducted a workshop on "Introduction to Machine Learning" on 15th January 2024.
    The event was held at Seminar Hall A, RIT. Around 45 students attended.
    Dr. Priya Sharma was the speaker. The student coordinators were Rahul and Sneha.
    Faculty coordinator was Prof. Anand Kumar.
    """


@pytest.fixture
def sample_event_facts():
    """Pre-populated EventFacts object for testing."""
    return EventFacts(
        event_title="Introduction to Machine Learning Workshop",
        date="2024-01-15",
        venue="Seminar Hall A, RIT",
        speaker_name="Dr. Priya Sharma",
        attendance_count=45,
        organizer="IEEE RIT Student Branch",
        student_coordinators=["Rahul", "Sneha"],
        faculty_coordinators=["Prof. Anand Kumar"],
        judges=[],
        volunteer_count=None,
        target_audience=None,
        mode="Offline",
        agenda=None,
        media_link=None,
        winners=[]
    )


@pytest.fixture
def sample_event_narrative():
    """Pre-populated EventNarrative object for testing."""
    return EventNarrative(
        executive_summary="The IEEE RIT Student Branch successfully conducted a workshop on 'Introduction to Machine Learning' on January 15, 2024. The event, held at Seminar Hall A, witnessed an enthusiastic participation of 45 students. Dr. Priya Sharma delivered an insightful session covering the fundamentals of machine learning.",
        key_takeaways=[
            "Introduction to core ML concepts and algorithms",
            "Hands-on experience with real-world datasets",
            "Networking opportunity with industry experts"
        ]
    )


@pytest.fixture
def sample_full_report(sample_event_facts, sample_event_narrative):
    """Complete report combining facts and narrative."""
    return FullReport(
        facts=sample_event_facts,
        narrative=sample_event_narrative,
        confidence_score=0.95
    )


@pytest.fixture
def sample_winners():
    """Sample winner data for hackathon-style events."""
    return [
        Winner(
            place="First Place",
            prize_money="₹10,000",
            team_name="CodeCrafters",
            members=["Alice", "Bob", "Charlie"]
        ),
        Winner(
            place="Second Place",
            prize_money="₹5,000",
            team_name="ByteBuilders",
            members=["Dave", "Eve"]
        )
    ]


# --- Mock Fixtures ---

@pytest.fixture
def mock_gemini_client():
    """Mocked Gemini client that returns controlled responses."""
    with patch('core.llm.genai.Client') as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_auditor_response(sample_event_facts):
    """Mock response object for auditor calls."""
    mock_response = Mock()
    mock_response.parsed = sample_event_facts
    mock_response.text = sample_event_facts.model_dump_json()
    return mock_response


@pytest.fixture
def mock_ghostwriter_response(sample_event_narrative):
    """Mock response object for ghostwriter calls."""
    mock_response = Mock()
    mock_response.parsed = sample_event_narrative
    mock_response.text = sample_event_narrative.model_dump_json()
    return mock_response


@pytest.fixture
def mock_critic_safe_response():
    """Mock response for critic when report is safe."""
    mock_response = Mock()
    mock_response.text = "SAFE"
    return mock_response


@pytest.fixture
def mock_critic_issues_response():
    """Mock response for critic when hallucinations are found."""
    mock_response = Mock()
    mock_response.text = """
    - The report mentions 50 attendees but source says 45
    - Speaker title "Professor" not mentioned in source
    """
    return mock_response


# --- Environment Fixtures ---

@pytest.fixture(autouse=True)
def mock_env_api_key(monkeypatch):
    """Automatically set a fake API key for all tests."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-api-key-12345")
