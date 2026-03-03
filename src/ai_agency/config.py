"""Configuration management for AI Agency toolkit."""

import os
from pathlib import Path

from dotenv import load_dotenv

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
        return "gpt-4o"
    return "claude-sonnet-4-20250514"
