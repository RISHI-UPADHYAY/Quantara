from __future__ import annotations

from typing import Any

import requests

from app.services.research.research_copilot_service import ResearchLLMProvider


class OllamaProvider(ResearchLLMProvider):
    """
    Local Ollama LLM provider for Quantara's AI Research Copilot.

    This provider runs entirely against a locally installed Ollama server,
    so Quantara does not require a paid LLM API during development.
    """

    name = "ollama"

    def __init__(
        self,
        *,
        base_url: str = "http://127.0.0.1:11434",
        model: str = "llama3.2",
        timeout_seconds: int = 120,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        if not system_prompt or not system_prompt.strip():
            raise ValueError("system_prompt cannot be empty.")

        if not user_prompt or not user_prompt.strip():
            raise ValueError("user_prompt cannot be empty.")

        payload: dict[str, Any] = {
            "model": self.model,
            "system": system_prompt,
            "prompt": user_prompt,
            "stream": False,
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout_seconds,
            )
        except requests.RequestException as exc:
            raise RuntimeError(
                "Unable to connect to Ollama. "
                "Make sure Ollama is running and accessible at "
                f"{self.base_url}."
            ) from exc

        if response.status_code != 200:
            try:
                error_detail = response.json()
            except ValueError:
                error_detail = response.text

            raise RuntimeError(
                "Ollama request failed: "
                f"HTTP {response.status_code}: {error_detail}"
            )

        try:
            result = response.json()
        except ValueError as exc:
            raise RuntimeError(
                "Ollama returned an invalid JSON response."
            ) from exc

        answer = result.get("response")

        if not isinstance(answer, str) or not answer.strip():
            raise RuntimeError(
                "Ollama returned an empty research response."
            )

        return answer.strip()