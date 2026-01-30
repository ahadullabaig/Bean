"""
Gemini LLM Client Wrapper with Retry Logic and Caching.

Provides a singleton client with:
- Exponential backoff retry for transient failures
- Streamlit-compatible caching
- Centralized error handling
- Rate limit detection (no retry on 429)
"""
import os
import logging
from google import genai
from google.genai.errors import ClientError
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


class RateLimitError(Exception):
    """
    Custom exception for API rate limit errors.
    This should NOT be retried - user must wait.
    """
    def __init__(self, message: str = "API rate limit exceeded", retry_after: int = 60):
        self.message = message
        self.retry_after = retry_after
        super().__init__(self.message)


class AuthenticationError(Exception):
    """
    Custom exception for invalid API key errors.
    User needs to check/re-enter their API key.
    """
    def __init__(self, message: str = "Invalid API key. Please check your key and try again."):
        self.message = message
        super().__init__(self.message)


def is_rate_limit_error(error: Exception) -> bool:
    """Check if an exception is a rate limit (429) error."""
    if isinstance(error, ClientError) and error.status_code == 429:
        return True
    if isinstance(error, google_exceptions.ResourceExhausted):
        return True
    return False


def is_auth_error(error: Exception) -> bool:
    """Check if an exception is an authentication error (invalid API key)."""
    if isinstance(error, ClientError):
        # 401 = Unauthorized, 403 = Forbidden (both indicate invalid key)
        if error.status_code in (401, 403):
            return True
        # Also check for specific error messages
        error_str = str(error).lower()
        if "api key" in error_str or "invalid" in error_str or "unauthorized" in error_str:
            return True
    return False


# Exceptions that warrant a retry (transient failures)
# Note: ResourceExhausted (429) is intentionally EXCLUDED - we handle it separately
RETRYABLE_EXCEPTIONS = (
    google_exceptions.ServiceUnavailable,  # Temporary outage
    google_exceptions.DeadlineExceeded,    # Timeout
    ConnectionError,
    TimeoutError,
)


# Session-scoped client storage
# Key: api_key hash -> Client instance (prevents cross-session contamination)
_client_cache = {}


def get_gemini_client(api_key: str = None):
    """
    Returns a Gemini client instance for the given API key.
    
    Uses a cache keyed by the API key to avoid recreating clients,
    but each user session has its own key, preventing cross-session leaks.
    
    Args:
        api_key: The Gemini API key. If None, falls back to environment variable
                 (only for local development/testing).
    
    Raises:
        ValueError: If no API key is provided or found.
    """
    global _client_cache
    
    # Resolve API key
    key = api_key or os.getenv("GEMINI_API_KEY")
    if not key:
        raise ValueError("No API key provided. Please enter your Gemini API key.")
    
    # Return cached client for this key
    if key in _client_cache:
        return _client_cache[key]
    
    # Create and cache new client
    client = genai.Client(api_key=key)
    _client_cache[key] = client
    return client


def reset_client(api_key: str = None):
    """
    Reset the cached client for a specific API key.
    If no key provided, clears all cached clients.
    """
    global _client_cache
    if api_key:
        _client_cache.pop(api_key, None)
    else:
        _client_cache.clear()


def create_retry_decorator(max_attempts: int = 3, min_wait: int = 2, max_wait: int = 10):
    """
    Creates a retry decorator with exponential backoff.
    
    Note: Does NOT retry on rate limit (429) errors - those require user to wait.
    
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
