"""Live LLM Provider Interface supporting OpenAI-compatible and Claude APIs with retries and backoff."""

import time
from typing import Any, List, Optional

import httpx

from src.llm.base_provider import BaseLLMProvider, ChatMessage, LLMResponse
from src.utils.config import settings
from src.utils.logger import get_logger

logger = get_logger("live_provider")


class LiveLLMProvider(BaseLLMProvider):
    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.0,
        timeout_seconds: int = 30,
        max_retries: int = 3,
        backoff_factor: float = 1.5,
    ):
        super().__init__(model=model, temperature=temperature, timeout_seconds=timeout_seconds)
        self.api_key = api_key or settings.llm_api_key
        self.base_url = (base_url or settings.llm_base_url).rstrip("/")
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

    def generate(
        self,
        messages: List[ChatMessage],
        prompt_version: str,
        scenario_id: Optional[str] = None,
        scenario_context: Optional[str] = None,
        **kwargs: Any
    ) -> LLMResponse:
        if not self.api_key:
            raise ValueError("LiveLLMProvider requires a valid LLM_API_KEY in environment or constructor.")

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": self.temperature,
        }

        last_error = None
        for attempt in range(1, self.max_retries + 1):
            start_time = time.time()
            try:
                with httpx.Client(timeout=self.timeout_seconds) as client:
                    resp = client.post(url, headers=headers, json=payload)

                latency_ms = (time.time() - start_time) * 1000

                if resp.status_code == 200:
                    data = resp.json()
                    choice = data["choices"][0]
                    content = choice["message"]["content"]
                    usage = data.get("usage", {})

                    return LLMResponse(
                        content=content,
                        model=self.model,
                        prompt_version=prompt_version,
                        scenario_id=scenario_id,
                        latency_ms=latency_ms,
                        token_usage={
                            "prompt_tokens": usage.get("prompt_tokens", 0),
                            "completion_tokens": usage.get("completion_tokens", 0),
                            "total_tokens": usage.get("total_tokens", 0),
                        },
                        raw_metadata={"attempt": attempt, "finish_reason": choice.get("finish_reason")},
                        status="success",
                    )
                elif resp.status_code in [429, 500, 502, 503, 504]:
                    last_error = f"HTTP {resp.status_code}: {resp.text}"
                    sleep_time = self.backoff_factor ** attempt
                    logger.warning(f"Transient error on attempt {attempt}/{self.max_retries}. Retrying in {sleep_time:.1f}s... Details: {last_error}")
                    time.sleep(sleep_time)
                else:
                    # Non-retryable error (e.g. 400 Bad Request, 401 Unauthorized)
                    error_msg = f"Fatal HTTP {resp.status_code}: {resp.text}"
                    logger.error(error_msg)
                    return LLMResponse(
                        content="",
                        model=self.model,
                        prompt_version=prompt_version,
                        scenario_id=scenario_id,
                        latency_ms=(time.time() - start_time) * 1000,
                        status="error",
                        error_message=error_msg,
                    )

            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                last_error = str(exc)
                sleep_time = self.backoff_factor ** attempt
                logger.warning(f"Network error on attempt {attempt}/{self.max_retries}: {exc}. Retrying in {sleep_time:.1f}s...")
                time.sleep(sleep_time)
            except Exception as e:
                logger.error(f"Unexpected exception calling LLM API: {e}")
                return LLMResponse(
                    content="",
                    model=self.model,
                    prompt_version=prompt_version,
                    scenario_id=scenario_id,
                    latency_ms=(time.time() - start_time) * 1000,
                    status="error",
                    error_message=str(e),
                )

        return LLMResponse(
            content="",
            model=self.model,
            prompt_version=prompt_version,
            scenario_id=scenario_id,
            latency_ms=(time.time() - start_time) * 1000,
            status="error",
            error_message=f"Exceeded max retries ({self.max_retries}). Last error: {last_error}",
        )
