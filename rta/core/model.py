from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional


@dataclass(frozen=True)
class ChatMessage:
    role: str
    content: str


@dataclass(frozen=True)
class ModelResponse:
    content: str
    raw: Any = None


class Model(ABC):
    """Provider-neutral interface for language models used by agents."""

    @abstractmethod
    def chat(
        self,
        *,
        model: str,
        messages: List[ChatMessage],
        options: Optional[Mapping[str, Any]] = None,
    ) -> ModelResponse:
        """Generate a response from a sequence of chat messages."""

    @staticmethod
    def validate_request(
        model: str,
        messages: List[ChatMessage],
    ) -> None:
        if not model or not model.strip():
            raise ValueError("Model name must not be empty")
        if not messages:
            raise ValueError("At least one chat message is required")
        if any(not message.content for message in messages):
            raise ValueError("Chat message content must not be empty")
