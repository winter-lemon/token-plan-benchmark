"""Tests for the OpenAICompatProvider adapter."""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch

import openai
import pytest

from token_plan_benchmark.core.exceptions import (
    ConfigurationError,
    ProviderError,
    RateLimitError,
)
from token_plan_benchmark.core.models import ModelConfig, ProviderConfig, TestCase, TokenTiming
from token_plan_benchmark.providers.adapter import DEFAULT_TIMEOUT, OpenAICompatProvider


# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def provider_config() -> ProviderConfig:
    return ProviderConfig(
        name="aliyun",
        display_name="阿里云百炼",
        adapter="generic_openai_compat",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key_env="DASHSCOPE_API_KEY",
    )


@pytest.fixture
def model_config() -> ModelConfig:
    return ModelConfig(
        model_id="qwen-plus",
        display_name="Qwen-Plus",
        provider="aliyun",
        max_tokens=4096,
    )


@pytest.fixture
def test_case() -> TestCase:
    return TestCase(
        id="short_answer",
        name="简短回答",
        prompt="解释什么是 CPU 缓存",
        expected_output_tokens=80,
        category="short",
    )


@pytest.fixture
def test_case_with_system() -> TestCase:
    return TestCase(
        id="with_system",
        name="带系统提示",
        prompt="你好",
        system_prompt="你是一个有帮助的助手",
        expected_output_tokens=50,
        category="short",
    )


# ── Helper ────────────────────────────────────────────────────────────


def _make_chunk(content: str | None) -> MagicMock:
    """Build a mock OpenAI streaming chunk with the given delta content.

    Pass ``None`` to create a chunk with no choices (e.g., a usage-only chunk).
    """
    if content is None:
        chunk = MagicMock()
        # Simulate a chunk with no choices (usage-only, etc.)
        chunk.choices = []
        return chunk

    delta = MagicMock()
    delta.content = content
    choice = MagicMock()
    choice.delta = delta
    choice.index = 0
    chunk = MagicMock()
    chunk.choices = [choice]
    return chunk


class _AsyncStream:
    """Async iterator wrapping a list of mock chunks."""

    def __init__(self, chunks: list[MagicMock]) -> None:
        self._chunks = chunks
        self._idx = 0

    def __aiter__(self) -> _AsyncStream:
        return self

    async def __anext__(self) -> MagicMock:
        if self._idx >= len(self._chunks):
            raise StopAsyncIteration
        chunk = self._chunks[self._idx]
        self._idx += 1
        return chunk


# ── Initialization tests ──────────────────────────────────────────────


def test_init_with_valid_config_creates_async_client(provider_config):
    """4.2 Client created with correct base_url and API key."""
    with patch.dict(os.environ, {"DASHSCOPE_API_KEY": "test-key-123"}):
        with patch.object(openai, "AsyncOpenAI") as mock_client_cls:
            provider = OpenAICompatProvider(provider_config)
            mock_client_cls.assert_called_once()

            call_kwargs = mock_client_cls.call_args.kwargs
            assert call_kwargs["api_key"] == "test-key-123"
            assert call_kwargs["base_url"] == provider_config.base_url
            assert call_kwargs["timeout"] == DEFAULT_TIMEOUT

            assert provider._client is mock_client_cls.return_value


def test_init_missing_api_key_raises_configuration_error(provider_config):
    """4.3 Missing env var raises ConfigurationError."""
    # Ensure the env var is NOT set
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ConfigurationError, match="DASHSCOPE_API_KEY"):
            OpenAICompatProvider(provider_config)


def test_init_default_timeout_applied(provider_config):
    """4.9a Default 60s timeout when not specified."""
    with patch.dict(os.environ, {"DASHSCOPE_API_KEY": "test-key"}):
        with patch.object(openai, "AsyncOpenAI") as mock_cls:
            OpenAICompatProvider(provider_config)
            assert mock_cls.call_args.kwargs["timeout"] == DEFAULT_TIMEOUT


def test_init_custom_timeout_from_extra_body():
    """4.9b Custom timeout from ProviderConfig.extra_body."""
    config = ProviderConfig(
        name="tencent",
        display_name="腾讯混元",
        adapter="generic_openai_compat",
        base_url="https://api.hunyuan.cloud.tencent.com/v1",
        api_key_env="HUNYUAN_API_KEY",
        extra_body={"timeout": 30.0},
    )
    with patch.dict(os.environ, {"HUNYUAN_API_KEY": "test-key"}):
        with patch.object(openai, "AsyncOpenAI") as mock_cls:
            OpenAICompatProvider(config)
            assert mock_cls.call_args.kwargs["timeout"] == 30.0


# ── Streaming tests ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_generate_stream_yields_token_timing_records(
    provider_config, model_config, test_case
):
    """4.4 Streaming yields correct TokenTiming records."""
    chunks = [
        _make_chunk("Hello"),
        _make_chunk(","),
        _make_chunk("World"),
    ]

    with patch.dict(os.environ, {"DASHSCOPE_API_KEY": "test-key"}):
        with patch.object(openai, "AsyncOpenAI") as mock_cls:
            mock_client = mock_cls.return_value
            mock_client.chat.completions.create = AsyncMock(
                return_value=_AsyncStream(chunks)
            )

            provider = OpenAICompatProvider(provider_config)
            tokens = [t async for t in provider.generate_stream(model_config, test_case)]

    assert len(tokens) == 3
    assert tokens[0].token_index == 0
    assert tokens[0].text == "Hello"
    assert tokens[1].token_index == 1
    assert tokens[1].text == ","
    assert tokens[2].token_index == 2
    assert tokens[2].text == "World"

    # Inter-token latency: first token is 0, others are positive (except for zero-length mock chunks)
    assert tokens[0].inter_token_latency_ms == 0.0


@pytest.mark.asyncio
async def test_ttft_is_measured_correctly(provider_config, model_config, test_case):
    """4.5 TTFT (arrival_time_s) is measured from request start."""
    chunks = [_make_chunk("First")]

    with patch.dict(os.environ, {"DASHSCOPE_API_KEY": "test-key"}):
        with patch.object(openai, "AsyncOpenAI") as mock_cls:
            mock_client = mock_cls.return_value
            mock_client.chat.completions.create = AsyncMock(
                return_value=_AsyncStream(chunks)
            )

            provider = OpenAICompatProvider(provider_config)
            tokens = [t async for t in provider.generate_stream(model_config, test_case)]

    assert len(tokens) == 1
    # arrival_time_s should be a positive float (time elapsed since request start)
    assert isinstance(tokens[0].arrival_time_s, float)
    assert tokens[0].arrival_time_s > 0
    assert tokens[0].inter_token_latency_ms == 0.0


@pytest.mark.asyncio
async def test_empty_content_chunks_are_skipped(provider_config, model_config, test_case):
    """4.6 Empty/whitespace-only delta.content yields no TokenTiming."""
    chunks = [
        _make_chunk(""),           # empty
        _make_chunk("  "),         # whitespace-only
        _make_chunk("Real"),       # content
        _make_chunk("\n"),         # whitespace newline
        _make_chunk(None),         # delta.content is None → treated as empty
        _make_chunk("End"),
    ]

    with patch.dict(os.environ, {"DASHSCOPE_API_KEY": "test-key"}):
        with patch.object(openai, "AsyncOpenAI") as mock_cls:
            mock_client = mock_cls.return_value
            mock_client.chat.completions.create = AsyncMock(
                return_value=_AsyncStream(chunks)
            )

            provider = OpenAICompatProvider(provider_config)
            tokens = [t async for t in provider.generate_stream(model_config, test_case)]

    texts = [t.text for t in tokens]
    assert texts == ["Real", "End"]
    assert tokens[0].token_index == 0
    assert tokens[1].token_index == 1


@pytest.mark.asyncio
async def test_stream_with_system_prompt(
    provider_config, model_config, test_case_with_system
):
    """System prompt is passed as a message."""
    chunks = [_make_chunk("Ok")]

    with patch.dict(os.environ, {"DASHSCOPE_API_KEY": "test-key"}):
        with patch.object(openai, "AsyncOpenAI") as mock_cls:
            mock_client = mock_cls.return_value
            mock_client.chat.completions.create = AsyncMock(
                return_value=_AsyncStream(chunks)
            )

            provider = OpenAICompatProvider(provider_config)
            _ = [t async for t in provider.generate_stream(model_config, test_case_with_system)]

    call_args = mock_client.chat.completions.create.call_args.kwargs
    assert len(call_args["messages"]) == 2
    assert call_args["messages"][0] == {"role": "system", "content": "你是一个有帮助的助手"}
    assert call_args["messages"][1] == {"role": "user", "content": "你好"}


@pytest.mark.asyncio
async def test_stream_completes_without_error(provider_config, model_config, test_case):
    """Stream completes normally — no exception raised."""
    chunks = [_make_chunk("Done")]

    with patch.dict(os.environ, {"DASHSCOPE_API_KEY": "test-key"}):
        with patch.object(openai, "AsyncOpenAI") as mock_cls:
            mock_client = mock_cls.return_value
            mock_client.chat.completions.create = AsyncMock(
                return_value=_AsyncStream(chunks)
            )

            provider = OpenAICompatProvider(provider_config)
            tokens = [t async for t in provider.generate_stream(model_config, test_case)]

    assert len(tokens) == 1


# ── Error handling tests ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_rate_limit_error_mapped(provider_config, model_config, test_case):
    """4.7 RateLimitError raised on HTTP 429."""
    with patch.dict(os.environ, {"DASHSCOPE_API_KEY": "test-key"}):
        with patch.object(openai, "AsyncOpenAI") as mock_cls:
            mock_client = mock_cls.return_value
            mock_client.chat.completions.create = AsyncMock(
                side_effect=openai.RateLimitError(
                    message="Too many requests",
                    response=MagicMock(status_code=429),
                    body=None,
                )
            )

            provider = OpenAICompatProvider(provider_config)
            with pytest.raises(RateLimitError, match="Too many requests"):
                _ = [token async for token in provider.generate_stream(model_config, test_case)]


@pytest.mark.asyncio
async def test_api_status_error_mapped_to_provider_error(
    provider_config, model_config, test_case
):
    """4.8 APIStatusError → ProviderError with status code."""
    with patch.dict(os.environ, {"DASHSCOPE_API_KEY": "test-key"}):
        with patch.object(openai, "AsyncOpenAI") as mock_cls:
            mock_client = mock_cls.return_value
            mock_client.chat.completions.create = AsyncMock(
                side_effect=openai.APIStatusError(
                    message="Invalid API Key",
                    response=MagicMock(status_code=401),
                    body=None,
                )
            )

            provider = OpenAICompatProvider(provider_config)
            with pytest.raises(ProviderError, match=r"\[401\] Invalid API Key"):
                _ = [token async for token in provider.generate_stream(model_config, test_case)]


@pytest.mark.asyncio
async def test_generic_exception_mapped_to_provider_error(
    provider_config, model_config, test_case
):
    """Non-openai exceptions also mapped to ProviderError."""
    with patch.dict(os.environ, {"DASHSCOPE_API_KEY": "test-key"}):
        with patch.object(openai, "AsyncOpenAI") as mock_cls:
            mock_client = mock_cls.return_value
            mock_client.chat.completions.create = AsyncMock(
                side_effect=ValueError("Something unexpected")
            )

            provider = OpenAICompatProvider(provider_config)
            with pytest.raises(ProviderError, match="Something unexpected"):
                _ = [token async for token in provider.generate_stream(model_config, test_case)]


@pytest.mark.asyncio
async def test_stream_uses_model_id_and_max_tokens(
    provider_config, model_config, test_case
):
    """Model config fields are passed to the API call."""
    chunks = [_make_chunk("x")]

    with patch.dict(os.environ, {"DASHSCOPE_API_KEY": "test-key"}):
        with patch.object(openai, "AsyncOpenAI") as mock_cls:
            mock_client = mock_cls.return_value
            mock_client.chat.completions.create = AsyncMock(
                return_value=_AsyncStream(chunks)
            )

            provider = OpenAICompatProvider(provider_config)
            _ = [t async for t in provider.generate_stream(model_config, test_case)]

    call_args = mock_client.chat.completions.create.call_args.kwargs
    assert call_args["model"] == model_config.model_id
    assert call_args["max_tokens"] == model_config.max_tokens
    assert call_args["stream"] is True
