from unittest.mock import MagicMock, patch
from core.critic import check_consistency

@patch("core.llm.genai.Client")
@patch("os.getenv")
def test_critic_safe(mock_getenv, mock_client_class):
    """Test critic returns empty list when safe."""
    mock_getenv.return_value = "fake_key"
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    
    # Simulate SAFE response
    mock_response = MagicMock()
    mock_response.text = "SAFE"
    mock_client.models.generate_content.return_value = mock_response
    
    issues = check_consistency("source", "report")
    assert issues == []

@patch("core.llm.genai.Client")
@patch("os.getenv")
def test_critic_issues(mock_getenv, mock_client_class):
    """Test critic parses issues correctly."""
    mock_getenv.return_value = "fake_key"
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    
    # Simulate Issues response
    mock_response = MagicMock()
    mock_response.text = "- Date mismatch\n- Wrong speaker"
    mock_client.models.generate_content.return_value = mock_response
    
    issues = check_consistency("source", "report")
    assert len(issues) == 2
    assert "Date mismatch" in issues
