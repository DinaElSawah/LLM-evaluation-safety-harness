"""
Anthropic provider. Requires `pip install anthropic` and an ANTHROPIC_API_KEY.

Not imported by the test suite's mocked runs — only needed when you actually
point the harness at a real Claude model.
"""
from __future__ import annotations

import os

from .base import LLMProvider


class AnthropicProvider(LLMProvider):
    def __init__(self, model_name: str = "claude-sonnet-4-6", api_key: str | None = None):
        try:
            import anthropic  # local import: don't require this dependency unless used
        except ImportError as e:
            raise ImportError(
                "AnthropicProvider requires the 'anthropic' package. Install with: pip install anthropic"
            ) from e

        key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise ValueError(
                "No Anthropic API key found. Set ANTHROPIC_API_KEY in your environment or .env file."
            )
        self.model_name = model_name
        self._client = anthropic.Anthropic(api_key=key)

    def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        kwargs = {
            "model": self.model_name,
            "max_tokens": 1024,
            "temperature": 0.2,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        response = self._client.messages.create(**kwargs)
        # Concatenate all text blocks in case the response has more than one
        return "".join(block.text for block in response.content if hasattr(block, "text"))
