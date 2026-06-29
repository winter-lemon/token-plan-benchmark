"""Provider adapters for OpenAI-compatible LLM endpoints.

Each provider (Aliyun Bailian, Tencent Hunyuan, ByteDance Volcano Engine)
uses the same OpenAI-compatible API, so a single adapter class handles all.
"""

from __future__ import annotations

import os
import time
from typing import AsyncIterator

import openai

from token_plan_benchmark.core.exceptions import (
    ConfigurationError,
    ProviderError,
    RateLimitError,
)
from token_plan_benchmark.core.models import ModelConfig, ProviderConfig, TestCase, TokenTiming

__all__ = ["OpenAICompatProvider"]

DEFAULT_TIMEOUT = 60.0


class OpenAICompatProvider:
    """Async streaming adapter for OpenAI-compatible LLM providers.

    Configures an ``AsyncOpenAI`` client from a :class:`ProviderConfig` and
    exposes ``generate_stream`` to produce per-token timing records.
    """

    def __init__(self, config: ProviderConfig) -> None:
        api_key = os.getenv(config.api_key_env)
        if not api_key:
            raise ConfigurationError(
                f"API key not found in environment variable: {config.api_key_env}"
            )

        base_url = config.base_url
        if config.base_url_env:
            env_url = os.getenv(config.base_url_env)
            if env_url:
                base_url = env_url

        timeout: float = DEFAULT_TIMEOUT
        if config.extra_body:
            timeout = float(config.extra_body.get("timeout", DEFAULT_TIMEOUT))

        self._client = openai.AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            default_headers=config.extra_headers or None,
            timeout=timeout,
        )

    async def generate_stream(
        self,
        model_config: ModelConfig,
        test_case: TestCase,
    ) -> AsyncIterator[TokenTiming]:
        """Stream tokens from the provider and yield timing records.

        Parameters
        ----------
        model_config:
            The model to call (carries ``model_id`` and ``max_tokens``).
        test_case:
            The benchmark test case (carries ``prompt`` and optional
            ``system_prompt``).

        Yields
        ------
        TokenTiming
            One record per content-bearing token, with arrival timestamp
            and inter-token latency.
        """
        messages: list[dict[str, str]] = []
        if test_case.system_prompt:
            messages.append({"role": "system", "content": test_case.system_prompt})
        messages.append({"role": "user", "content": test_case.prompt})

        start_time = time.perf_counter()
        prev_arrival = start_time
        token_index = 0

        try:
            stream = await self._client.chat.completions.create(
                model=model_config.model_id,
                messages=messages,
                max_tokens=model_config.max_tokens,
                stream=True,
            )

            async for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                if not delta.content or not delta.content.strip():
                    continue

                now = time.perf_counter()
                arrival_time_s = now - start_time
                inter_token_latency_ms = (
                    0.0 if token_index == 0
                    else max(0.0, (now - prev_arrival) * 1000.0)
                )

                yield TokenTiming(
                    token_index=token_index,
                    text=delta.content,
                    arrival_time_s=arrival_time_s,
                    inter_token_latency_ms=inter_token_latency_ms,
                )

                prev_arrival = now
                token_index += 1

        except openai.RateLimitError as exc:
            raise RateLimitError(str(exc)) from exc
        except openai.APIStatusError as exc:
            raise ProviderError(f"[{exc.status_code}] {exc.message}") from exc
        except Exception as exc:
            raise ProviderError(str(exc)) from exc
