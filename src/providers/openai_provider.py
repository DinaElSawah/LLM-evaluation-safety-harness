"""
OpenAI provider. Requires `pip install openai` and an OPENAI_API_KEY.

Not imported by the test suite's mocked runs — only needed when you actually
point the harness at a real OpenAI model.
"""
from __future__ import annotations

import os

from .base import LLMProvider


class OpenAIProvider(LLMProvider):
    def __init__(self, model_name: str = "gpt-4o", api_key: str | None = None):
        try:
            import openai  # local import: don't require this dependency unless used
        except ImportError as e:
            raise ImportError(
                "OpenAIProvider requires the 'openai' package. Install with: pip install openai"
            ) from e

        key = api_key or os.environ.get("OPENAI_API_KEY")
        if not key:
            raise ValueError(
                "No OpenAI API key found. Set OPENAI_API_KEY in your environment or .env file."
            )
        self.model_name = model_name
        self._client = openai.OpenAI(api_key=key)

    def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self._client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=0.2,
        )
        return response.choices[0].message.content or ""
