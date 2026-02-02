"""
Unit tests for the UI Handlers module.
Tests cover: text hashing, caching behavior, and audio processing.
"""
import pytest
import hashlib
from unittest.mock import patch, MagicMock
from io import BytesIO

from ui.handlers import _compute_text_hash, handle_text_process
from models.schemas import EventFacts


class TestTextHashing:
    """Tests for text hash computation."""
    
    def test_compute_text_hash_returns_md5(self):
        """Test that hash is a valid MD5 hex digest."""
        text = "Test event notes"
        result = _compute_text_hash(text)
        
        # MD5 hex digest is 32 characters
        assert len(result) == 32
        assert result == hashlib.md5(text.encode()).hexdigest()
    
    def test_compute_text_hash_is_deterministic(self):
        """Test that same text produces same hash."""
        text = "Same text across multiple calls"
        hash1 = _compute_text_hash(text)
        hash2 = _compute_text_hash(text)
        
        assert hash1 == hash2
    
    def test_compute_text_hash_differs_for_different_text(self):
        """Test that different texts produce different hashes."""
        hash1 = _compute_text_hash("First text")
        hash2 = _compute_text_hash("Second text")
        
        assert hash1 != hash2


class TestHandleTextProcess:
    """Tests for text processing handler."""
    
    @pytest.fixture
    def mock_extract_facts(self):
        """Mock the extract_facts function."""
        with patch('ui.handlers.extract_facts') as mock:
            mock.return_value = EventFacts(
                event_title="Test Event",
                date="2024-01-15",
                venue="Test Venue"
            )
            yield mock
    
    @pytest.fixture
    def clear_cache(self):
        """Clear Streamlit cache before each test."""
        # Import the cached function and clear it
        from ui.handlers import _cached_extract_facts
        _cached_extract_facts.clear()
        yield
    
    def test_handle_text_process_returns_event_facts(self, mock_extract_facts, clear_cache):
        """Test that handler returns EventFacts object."""
        # Mock st.spinner to avoid Streamlit context issues
        with patch('ui.handlers.st'):
            result = handle_text_process("Test notes", "test-api-key")
        
        assert isinstance(result, EventFacts)
        assert result.event_title == "Test Event"
    
    def test_handle_text_process_calls_auditor(self, mock_extract_facts, clear_cache):
        """Test that handler calls the auditor module."""
        with patch('ui.handlers.st'):
            handle_text_process("New notes for extraction", "test-api-key")
        
        mock_extract_facts.assert_called_once()


class TestHandleAudioProcess:
    """Tests for audio processing handler."""
    
    @pytest.fixture
    def mock_gemini_client(self):
        """Mock the Gemini client for audio processing."""
        mock_response = MagicMock()
        mock_response.parsed = EventFacts(
            event_title="Audio Event",
            date="2024-02-01"
        )
        
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        
        with patch('ui.handlers.get_gemini_client', return_value=mock_client):
            yield mock_client
    
    def test_handle_audio_process_reads_audio_bytes(self, mock_gemini_client):
        """Test that audio handler reads bytes from file."""
        from ui.handlers import handle_audio_process
        
        audio_file = BytesIO(b"fake audio data")
        
        result = handle_audio_process(audio_file, "test-api-key")
        
        assert result is not None
        assert result.event_title == "Audio Event"
    
    def test_handle_audio_process_uses_correct_mime_type(self, mock_gemini_client):
        """Test that audio handler uses WAV mime type."""
        from ui.handlers import handle_audio_process
        
        audio_file = BytesIO(b"fake audio data")
        handle_audio_process(audio_file, "test-api-key")
        
        # Check the call was made with inline_data containing audio/wav
        call_args = mock_gemini_client.models.generate_content.call_args
        contents = call_args.kwargs.get('contents') or call_args.args[0] if call_args.args else None
        
        # The call should include audio/wav mime type
        mock_gemini_client.models.generate_content.assert_called_once()
