from unittest.mock import MagicMock, patch
from core.critic import check_consistency

@patch("google.generativeai.GenerativeModel")
@patch("os.getenv")
def test_critic_safe(mock_getenv, mock_model_class):
    """Test critic returns empty list when safe."""
    mock_getenv.return_value = "fake_key"
    mock_model_instance = MagicMock()
    mock_model_class.return_value = mock_model_instance
    
    # Simulate SAFE response
    mock_response = MagicMock()
    mock_response.text = "SAFE"
    mock_model_instance.generate_content.return_value = mock_response
    
    issues = check_consistency("source", "report")
    assert issues == []

@patch("google.generativeai.GenerativeModel")
@patch("os.getenv")
def test_critic_issues(mock_getenv, mock_model_class):
    """Test critic parses issues correctly."""
    mock_getenv.return_value = "fake_key"
    mock_model_instance = MagicMock()
    mock_model_class.return_value = mock_model_instance
    
    # Simulate Issues response
    mock_response = MagicMock()
    mock_response.text = "- Date mismatch\n- Wrong speaker"
    mock_model_instance.generate_content.return_value = mock_response
    
    issues = check_consistency("source", "report")
    assert len(issues) == 2
    assert "Date mismatch" in issues
