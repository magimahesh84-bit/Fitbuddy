"""
gemini_service.py - Centralized Gemini client and resilient request execution.

Handles Google GenAI API calls with distinct handling for:
- 429 Daily Free-Tier Quota Exceeded (no wasteful retries, clean quota error)
- 429 Temporary Rate Limiting (short-term exponential backoff)
- 503 Temporary High Demand (exponential backoff and model fallback)
- Authentication & Model availability errors (immediate fail-fast)
"""

import os
import time
import random
import logging
from google import genai
from dotenv import load_dotenv

from app.gemini_config import (
    GEMINI_WORKOUT_MODEL,
    GEMINI_NUTRITION_MODEL,
    GEMINI_UPDATE_MODEL,
    GEMINI_FALLBACK_MODEL,
)

load_dotenv()
logger = logging.getLogger("fitbuddy.gemini")


# ─── Custom Exceptions ───────────────────────────────────────────────────────
class GeminiError(Exception):
    """Base exception for Gemini operations."""
    pass


class GeminiQuotaError(GeminiError):
    """Raised when the daily free-tier API quota is exhausted."""
    pass


class GeminiRateLimitError(GeminiError):
    """Raised when short-term rate limits are temporarily exceeded."""
    pass


class GeminiCapacityError(GeminiError):
    """Raised when temporary service capacity (503) prevents generation."""
    pass


class GeminiAuthError(GeminiError):
    """Raised when API key is missing or authentication fails."""
    pass


class GeminiModelError(GeminiError):
    """Raised when a requested Gemini model is unavailable or unsupported."""
    pass


def get_gemini_client() -> genai.Client:
    """
    Create and return a Gemini API client using the key from environment variables.
    Supports GEMINI_API_KEY (preferred) and GOOGLE_API_KEY (backward compatibility).

    Raises:
        GeminiAuthError: If no valid API key is configured.
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key or api_key in ("your_google_api_key_here", "your_gemini_api_key_here"):
        raise GeminiAuthError(
            "Gemini API authentication failed. Please check the API configuration."
        )
    return genai.Client(api_key=api_key)


# ─── Error Classification Helpers ────────────────────────────────────────────
def is_daily_quota_error(error: Exception) -> bool:
    """
    Check if an error represents daily free-tier quota exhaustion.
    Crucial: Daily quota cannot be restored by retries, so we must fail immediately.
    """
    err_str = str(error).upper()
    is_quota_string = any(marker in err_str for marker in (
        "GENERATEREQUESTSPERDAY",
        "PERDAY",
        "PER_DAY",
        "DAILY",
        "FREE_TIER_REQUESTS",
        "FREE TIER REQUESTS",
        "QUOTA EXCEEDED FOR METRIC",
    ))
    has_code_or_status = any(marker in err_str for marker in ("429", "RESOURCE_EXHAUSTED", "QUOTA"))
    return is_quota_string and has_code_or_status


def is_temporary_rate_limit(error: Exception) -> bool:
    """
    Check if an error represents a temporary short-term rate limit (e.g. RPM / requests per minute)
    rather than an exhausted daily quota.
    """
    if is_daily_quota_error(error):
        return False
    err_str = str(error).upper()
    return any(marker in err_str for marker in (
        "429", "RESOURCE_EXHAUSTED", "RATE LIMIT", "RATE_LIMIT",
        "REQUESTS PER MINUTE", "REQUESTSPERMINUTE"
    ))


def is_503_unavailable(error: Exception) -> bool:
    """Check if an error represents temporary high demand or server unavailable."""
    err_str = str(error).upper()
    return any(marker in err_str for marker in (
        "503", "UNAVAILABLE", "HIGH DEMAND", "TEMPORARILY"
    ))


def is_auth_error(error: Exception) -> bool:
    """Check if an error represents an authentication or authorization failure."""
    err_str = str(error).upper()
    return any(marker in err_str for marker in (
        "API_KEY_INVALID", "INVALID API KEY", "UNAUTHENTICATED",
        "PERMISSION_DENIED", "401", "403"
    )) or ("400" in err_str and "KEY" in err_str)


def is_model_error(error: Exception) -> bool:
    """Check if an error represents a model not found / unsupported error."""
    err_str = str(error).upper()
    return any(marker in err_str for marker in (
        "404", "NOT_FOUND", "NOT FOUND", "IS NO LONGER AVAILABLE"
    ))


def format_user_friendly_error(error: Exception) -> str:
    """Format technical exceptions into clean, user-friendly error messages (Step 12)."""
    if isinstance(error, GeminiAuthError) or is_auth_error(error):
        return "Gemini API authentication failed. Please check the API configuration."
    if isinstance(error, GeminiQuotaError) or is_daily_quota_error(error):
        return "Gemini's daily API quota has been reached. Please try again after the quota resets."
    if isinstance(error, GeminiCapacityError) or is_503_unavailable(error):
        return "Gemini is temporarily busy. Please try again in a few moments."
    if isinstance(error, GeminiRateLimitError):
        return "Gemini is temporarily rate-limited. Please try again shortly."
    if isinstance(error, GeminiModelError):
        return "The configured Gemini model is currently unavailable."

    err_str = str(error)
    # Check for raw technical error indicators
    err_upper = err_str.upper()
    if any(m in err_upper for m in ("RESOURCE_EXHAUSTED", "QUOTA", "GENERATEREQUESTS")):
        return "Gemini's daily API quota has been reached. Please try again after the quota resets."
    if any(m in err_upper for m in ("503", "UNAVAILABLE", "HIGH DEMAND")):
        return "Gemini is temporarily busy. Please try again in a few moments."
    if any(m in err_upper for m in ("401", "403", "API_KEY", "UNAUTHENTICATED")):
        return "Gemini API authentication failed. Please check the API configuration."
    if "{" in err_str and "}" in err_str:
        return "Gemini service encountered an error. Please try again later."
    return err_str


# ─── Resilient Gemini Request Runner ─────────────────────────────────────────
def call_gemini_with_retry(
    prompt: str,
    primary_model: str,
    fallback_model: str = None,
    max_retries: int = 3,
) -> str:
    """
    Execute a Gemini text generation call with intelligent retry and quota detection.

    Behavior:
      1. Attempt generation with primary_model.
      2. If 429 Daily Quota Exceeded occurs:
         - DO NOT retry.
         - DO NOT call fallback if fallback model shares the exhausted quota.
         - Raise GeminiQuotaError immediately to save resources and avoid spamming.
      3. If 429 Temporary Rate Limit occurs (RPM):
         - Wait with exponential backoff (2s, 4s, 8s) + jitter, retry up to max_retries.
      4. If 503 UNAVAILABLE occurs:
         - Retry with exponential backoff (2s, 4s, 8s) + jitter.
         - If retries on primary fail, try fallback_model.
      5. If authentication fails:
         - Fail immediately (no retries).
      6. Never expose API key in logs or exceptions.

    Args:
        prompt: The text prompt for generation.
        primary_model: Primary model to use.
        fallback_model: Optional fallback model (used ONLY for 503 capacity / model errors,
                        never for daily quota exhaustion).
        max_retries: Maximum attempts for transient errors (default: 3).

    Returns:
        Generated text string.
    """
    client = get_gemini_client()

    models_to_try = [primary_model]
    # Fallback model is only considered if distinct from primary
    if fallback_model and fallback_model != primary_model:
        models_to_try.append(fallback_model)

    retry_delays = [2.0, 4.0, 8.0]
    last_transient_error = None

    for m_index, current_model in enumerate(models_to_try):
        is_fallback = m_index > 0
        if is_fallback:
            logger.info("Attempting fallback model: %s", current_model)

        for attempt in range(max_retries):
            try:
                # Step 6: Log exact model passed to API request
                print(f"Gemini request model: {current_model}", flush=True)
                logger.info("Gemini request model: %s (attempt %d/%d)", current_model, attempt + 1, max_retries)
                # Step 9 & 15: Clean generation settings without deprecated parameters
                from google.genai import types
                gen_config = types.GenerateContentConfig(
                    temperature=0.7,
                )
                response = client.models.generate_content(
                    model=current_model,
                    contents=prompt,
                    config=gen_config,
                )
                if response and response.text:
                    logger.info("Successfully received response from model '%s'.", current_model)
                    return response.text
                raise GeminiError("No content returned by the AI model.")

            except Exception as e:
                # 1. Authentication / Invalid Key -> Fail immediately, never retry
                if is_auth_error(e):
                    logger.error("Gemini authentication failure with model '%s': %s", current_model, type(e).__name__)
                    raise GeminiAuthError(
                        "Gemini API authentication failed. Please check the API configuration."
                    ) from e

                # 2. Daily Quota Exceeded -> DO NOT RETRY, fail immediately
                if is_daily_quota_error(e):
                    logger.error(
                        "Gemini daily free-tier quota exhausted for model '%s'. Not retrying. Details: %s",
                        current_model, str(e)
                    )
                    raise GeminiQuotaError(
                        "Gemini's daily API quota has been reached. Please try again after the quota resets."
                    ) from e

                # 3. Model Not Found / Unsupported -> Do not retry same model, try fallback
                if is_model_error(e):
                    logger.warning("Gemini model '%s' unavailable: %s", current_model, e)
                    break

                # 4. Temporary Rate Limit (RPM) -> Exponential backoff on same model
                if is_temporary_rate_limit(e):
                    last_transient_error = e
                    logger.warning(
                        "Short-term rate limit for model '%s' (attempt %d/%d): %s",
                        current_model, attempt + 1, max_retries, str(e)
                    )
                    if attempt < max_retries - 1:
                        delay = retry_delays[min(attempt, len(retry_delays) - 1)] + random.uniform(0.1, 0.5)
                        logger.info("Waiting %.2fs for rate limit backoff...", delay)
                        time.sleep(delay)
                        continue
                    else:
                        logger.warning("Rate limit retries exhausted for '%s'.", current_model)
                        break

                # 5. 503 UNAVAILABLE (High Demand) -> Exponential backoff, then fallback
                if is_503_unavailable(e):
                    last_transient_error = e
                    logger.warning(
                        "Temporary 503 high demand for model '%s' (attempt %d/%d): %s",
                        current_model, attempt + 1, max_retries, str(e)
                    )
                    if attempt < max_retries - 1:
                        delay = retry_delays[min(attempt, len(retry_delays) - 1)] + random.uniform(0.1, 0.5)
                        logger.info("Waiting %.2fs for 503 backoff...", delay)
                        time.sleep(delay)
                        continue
                    else:
                        logger.warning("High demand retries exhausted for '%s'.", current_model)
                        break

                # 6. Any other unexpected error
                logger.error("Non-transient error with model '%s': %s", current_model, str(e))
                raise GeminiError(f"Gemini error: {str(e)}") from e

    # If we reached here, transient errors (503 / rate limits) exhausted all models
    if last_transient_error:
        if is_temporary_rate_limit(last_transient_error):
            raise GeminiRateLimitError("Gemini is temporarily rate-limited. Please try again shortly.")
        raise GeminiCapacityError("Gemini is temporarily busy. Please try again in a few moments.")

    raise GeminiModelError("The configured Gemini model is unavailable.")
