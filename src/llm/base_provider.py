"""Base LLM Provider Interface and Common Completion Objects."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(..., description="role: system, user, assistant")
    content: str = Field(..., description="message text")


class LLMResponse(BaseModel):
    content: str
    model: str
    prompt_version: str
    scenario_id: Optional[str] = None
    latency_ms: float
    token_usage: Dict[str, int] = Field(default_factory=lambda: {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
    raw_metadata: Dict[str, Any] = Field(default_factory=dict)
    status: str = "success"  # success, error, timeout
    error_message: Optional[str] = None


class BaseLLMProvider(ABC):
    """Abstract Base Class for LLM Providers."""

    def __init__(self, model: str, temperature: float = 0.0, timeout_seconds: int = 30):
        self.model = model
        self.temperature = temperature
        self.timeout_seconds = timeout_seconds

    @abstractmethod
    def generate(
        self,
        messages: List[ChatMessage],
        prompt_version: str,
        scenario_id: Optional[str] = None,
        scenario_context: Optional[str] = None,
        **kwargs: Any
    ) -> LLMResponse:
        """Synchronous chat completion generation."""
        pass
