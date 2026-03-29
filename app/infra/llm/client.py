from __future__ import annotations

import json
import re
from typing import Any, Dict, List

import httpx

from app.core.config import get_settings
from app.core.errors import LLMResponseError


class OpenAICompatibleLLMClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    def generate_json(
        self,
        *,
        schema_name: str,
        system_prompt: str,
        user_prompt: str,
    ) -> Dict[str, Any]:
        if not self.settings.openai_api_key:
            raise LLMResponseError("OPENAI_API_KEY is not configured")

        payload = {
            "model": self.settings.openai_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {self.settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        url = f"{self.settings.openai_base_url.rstrip('/')}/chat/completions"
        with httpx.Client(timeout=60.0) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()

        content = self._extract_content(response.json())
        try:
            return json.loads(self._strip_code_fences(content))
        except json.JSONDecodeError as exc:
            raise LLMResponseError(f"{schema_name} response is not valid JSON") from exc

    @staticmethod
    def _extract_content(payload: Dict[str, Any]) -> str:
        choices: List[Dict[str, Any]] = payload.get("choices", [])
        if not choices:
            raise LLMResponseError("LLM response contains no choices")
        message = choices[0].get("message", {})
        content = message.get("content", "")
        if isinstance(content, list):
            text_parts = [item.get("text", "") for item in content if item.get("type") == "text"]
            content = "\n".join(text_parts)
        if not isinstance(content, str) or not content.strip():
            raise LLMResponseError("LLM response content is empty")
        return content

    @staticmethod
    def _strip_code_fences(text: str) -> str:
        fenced = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text.strip(), re.DOTALL)
        return fenced.group(1) if fenced else text


def get_llm_client() -> OpenAICompatibleLLMClient:
    return OpenAICompatibleLLMClient()
