"""Provider Factory to instantiate Mock or Live Provider."""

from typing import Optional

from src.llm.base_provider import BaseLLMProvider
from src.llm.live_provider import LiveLLMProvider
from src.llm.mock_provider import MockLLMProvider
from src.utils.config import settings


def get_llm_provider(
    provider_type: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None
) -> BaseLLMProvider:
    p_type = (provider_type or settings.llm_provider).lower()
    m_name = model or settings.llm_model
    temp = temperature if temperature is not None else settings.llm_temperature

    if p_type == "live":
        return LiveLLMProvider(
            model=m_name,
            temperature=temp,
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            timeout_seconds=settings.llm_timeout_seconds,
            max_retries=settings.llm_max_retries
        )
    else:
        return MockLLMProvider(
            model=m_name,
            temperature=temp,
            timeout_seconds=settings.llm_timeout_seconds
        )
