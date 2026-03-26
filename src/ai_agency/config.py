"""Configuration management for AI Agency toolkit."""

import logging
import os
import subprocess
import time
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load .env from project root
_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(_env_path)


def get_provider() -> str:
    return os.getenv("AI_PROVIDER", "anthropic").lower()


def get_api_key() -> str:
    provider = get_provider()
    if provider == "anthropic":
        key = os.getenv("ANTHROPIC_API_KEY", "")
    elif provider == "openai":
        key = os.getenv("OPENAI_API_KEY", "")
    else:
        raise ValueError(f"Unknown AI provider: {provider}. Use 'anthropic' or 'openai'.")
    if not key:
        raise ValueError(
            f"No API key found for provider '{provider}'. "
            f"Set {'ANTHROPIC_API_KEY' if provider == 'anthropic' else 'OPENAI_API_KEY'} "
            f"in your .env file or environment."
        )
    return key


def get_model() -> str:
    model = os.getenv("AI_MODEL", "")
    if model:
        return model
    provider = get_provider()
    if provider == "anthropic":
        return "claude-sonnet-4-20250514"
    elif provider == "openai":
        return "gpt-5"
    return "claude-sonnet-4-20250514"


_stitch_token_cache: dict = {"token": "", "expires_at": 0.0}
_TOKEN_TTL = 50 * 60  # refresh every 50 minutes (tokens last ~60 min)


def _refresh_token_google_auth() -> str:
    """Refresh using google-auth library (works without gcloud CLI)."""
    try:
        import google.auth
        import google.auth.transport.requests

        creds, _ = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
        creds.refresh(google.auth.transport.requests.Request())
        if creds.token:
            return creds.token
    except Exception as e:
        logger.debug("google-auth refresh failed: %s", e)
    return ""


def _refresh_token_gcloud_cli() -> str:
    """Fallback: run gcloud CLI to get a fresh access token."""
    try:
        result = subprocess.run(
            ["gcloud", "auth", "application-default", "print-access-token"],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except FileNotFoundError:
        logger.debug("gcloud CLI not found")
    except Exception as e:
        logger.debug("gcloud CLI refresh error: %s", e)
    return ""


def get_stitch_token() -> str:
    """Get Stitch access token, auto-refreshing every ~50 min."""
    now = time.time()
    if _stitch_token_cache["token"] and now < _stitch_token_cache["expires_at"]:
        return _stitch_token_cache["token"]

    # Try auto-refresh: google-auth library first, then gcloud CLI
    token = _refresh_token_google_auth() or _refresh_token_gcloud_cli()
    if token:
        _stitch_token_cache["token"] = token
        _stitch_token_cache["expires_at"] = now + _TOKEN_TTL
        logger.info("Stitch token auto-refreshed")
        return token

    # Fallback to static .env value
    env_token = os.getenv("STITCH_ACCESS_TOKEN", "")
    if env_token:
        _stitch_token_cache["token"] = env_token
        _stitch_token_cache["expires_at"] = now + _TOKEN_TTL
    return env_token


def get_stitch_project_id() -> str:
    return os.getenv("STITCH_PROJECT_ID", "")


def get_stitch_api_key() -> str:
    return os.getenv("STITCH_API_KEY", "")
