"""
Gemini LLM Client Wrapper with Retry Logic and Caching.

Provides a singleton client with:
- Exponential backoff retry for transient failures
- Streamlit-compatible caching
- Centralized error handling
"""
import os
import logging
from google import genai
from google.api_core import exceptions as google_exceptions
from dotenv import load_dotenv
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

load_dotenv()

# Configure logging for retry visibility
logger = logging.getLogger(__name__)

# Default model to use across the application
DEFAULT_MODEL = "gemini-2.5-flash"

# Exceptions that warrant a retry (transient failures)
RETRYABLE_EXCEPTIONS = (
    google_exceptions.ResourceExhausted,  # Rate limit / quota
    google_exceptions.ServiceUnavailable,  # Temporary outage
    google_exceptions.DeadlineExceeded,    # Timeout
    ConnectionError,
    TimeoutError,
)


# Singleton client instance
_client_instance = None


def get_gemini_client():
    """
    Returns a cached Gemini client instance (singleton pattern).
    Raises ValueError if GEMINI_API_KEY is missing.
    
    Note: For Streamlit apps, consider using @st.cache_resource decorator
    on this function for proper lifecycle management.
    """
    global _client_instance
    
    if _client_instance is not None:
        return _client_instance
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables.")
    
    _client_instance = genai.Client(api_key=api_key)
    return _client_instance


def reset_client():
    """Reset the cached client (useful for testing or key rotation)."""
    global _client_instance
    _client_instance = None


def create_retry_decorator(max_attempts: int = 3, min_wait: int = 2, max_wait: int = 10):
    """
    Creates a retry decorator with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time between retries (seconds)
        max_wait: Maximum wait time between retries (seconds)
    
    Returns:
        A tenacity retry decorator
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True
    )


# Pre-configured retry decorator for LLM calls
llm_retry = create_retry_decorator(max_attempts=3, min_wait=2, max_wait=10)
