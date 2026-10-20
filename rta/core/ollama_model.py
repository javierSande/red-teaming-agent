import os
from typing import Any, List, Mapping, Optional

from .config import OLLAMA_HOST
from .model import ChatMessage, Model, ModelResponse

DEFAULT_OLLAMA_HOST = OLLAMA_HOST


class OllamaModel(Model):
    """Ollama implementation of the provider-neutral model interface."""

    def __init__(self, host: Optional[str] = None, client: Any = None):
        resolved_host = host or os.getenv("OLLAMA_HOST", DEFAULT_OLLAMA_HOST)
        if not resolved_host or not resolved_host.strip():
            raise ValueError("Ollama host must not be empty")

        if client is None:
            from ollama import Client

            client = Client(host=resolved_host.rstrip("/"))

        self.host = resolved_host.rstrip("/")
        self._client = client

    def chat(
        self,
        *,
        model: str,
        messages: List[ChatMessage],
        options: Optional[Mapping[str, Any]] = None,
    ) -> ModelResponse:
        self.validate_request(model, messages)
        response = self._client.chat(
            model=model,
            messages=[
                {"role": message.role, "content": message.content}
                for message in messages
            ],
            options=dict(options or {}),
        )
        message = response.get("message") if isinstance(response, dict) else response.message
        if isinstance(message, dict):
            content = message.get("content", "")
        else:
            content = getattr(message, "content", "")
        if not content:
            raise RuntimeError("Ollama returned an empty response")

        return ModelResponse(content=content, raw=response)
