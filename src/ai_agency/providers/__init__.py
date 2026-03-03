from ai_agency.config import get_provider
from ai_agency.providers.base import LLMProvider


def create_provider() -> LLMProvider:
    """Factory: create the configured LLM provider."""
    provider_name = get_provider()
    if provider_name == "anthropic":
        from ai_agency.providers.anthropic import AnthropicProvider

        return AnthropicProvider()
    elif provider_name == "openai":
        from ai_agency.providers.openai import OpenAIProvider

        return OpenAIProvider()
    else:
        raise ValueError(f"Unknown provider: {provider_name}. Use 'anthropic' or 'openai'.")


__all__ = ["LLMProvider", "create_provider"]
