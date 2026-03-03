"""OpenAI (GPT) LLM provider using instructor."""

from typing import TypeVar

import instructor
import openai
from pydantic import BaseModel

from ai_agency.config import get_api_key, get_model
from ai_agency.providers.base import LLMProvider

T = TypeVar("T", bound=BaseModel)


class OpenAIProvider(LLMProvider):
    """GPT-powered structured generation via instructor."""

    def __init__(self) -> None:
        raw_client = openai.OpenAI(api_key=get_api_key(), timeout=600.0)
        self.client = instructor.from_openai(raw_client)
        self.model = get_model()

    def generate_structured(
        self,
        prompt: str,
        response_model: type[T],
        system_prompt: str = "",
        max_retries: int = 2,
    ) -> T:
        messages: list[dict] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        return self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            response_model=response_model,
            max_retries=max_retries,
        )
