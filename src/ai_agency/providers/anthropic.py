"""Anthropic (Claude) LLM provider using instructor."""

from typing import TypeVar

import anthropic
import instructor
from pydantic import BaseModel

from ai_agency.config import get_api_key, get_model
from ai_agency.providers.base import LLMProvider

T = TypeVar("T", bound=BaseModel)


class AnthropicProvider(LLMProvider):
    """Claude-powered structured generation via instructor."""

    def __init__(self) -> None:
        raw_client = anthropic.Anthropic(api_key=get_api_key(), timeout=600.0)
        self.client = instructor.from_anthropic(raw_client)
        self.model = get_model()

    def generate_structured(
        self,
        prompt: str,
        response_model: type[T],
        system_prompt: str = "",
        max_retries: int = 2,
    ) -> T:
        messages = [{"role": "user", "content": prompt}]

        kwargs: dict = {
            "model": self.model,
            "max_tokens": 16000,
            "messages": messages,
            "response_model": response_model,
            "max_retries": max_retries,
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        return self.client.messages.create(**kwargs)
