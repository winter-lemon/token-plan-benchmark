## Why

The benchmark system needs to send streaming inference requests to three cloud LLM providers (Aliyun Bailian, Tencent Hunyuan, ByteDance Volcano Engine) and capture per-token timing data. All three providers expose OpenAI-compatible `/v1/chat/completions` endpoints, making a unified adapter pattern possible. Without this layer, the test runner cannot actually call any provider — it's the foundation the entire pipeline depends on.

## What Changes

- Create a `providers/` package under `src/token_plan_benchmark/` with a unified adapter interface
- Implement a single `OpenAICompatProvider` adapter that works with all three providers via different `base_url` + `api_key_env` configuration
- Provide an async streaming interface: `generate_stream(provider_config, model_config, test_case) → AsyncIterator[TokenTiming]`
- Calculate TTFT (time-to-first-token) by timestamping the first token arrival relative to request start
- Build per-token timing records (`TokenTiming`) with arrival time and inter-token latency
- Map OpenAI client errors to the existing exception hierarchy (`ProviderError`, `RateLimitError`)
- Add connection timeout handling (configurable per provider)
- Read API keys from environment variables as specified in `ProviderConfig.api_key_env`

## Capabilities

### New Capabilities
- `provider-adapters`: Unified async streaming adapter for OpenAI-compatible LLM providers, producing per-token timing records with TTFT computation and error classification

### Modified Capabilities
<!-- No existing specs are modified; this is a new capability. -->

## Impact

- **New module**: `src/token_plan_benchmark/providers/` (currently only has `__init__.py`)
- **Depends on**: `core/models.py` (ProviderConfig, ModelConfig, TestCase, TokenTiming), `core/exceptions.py` (ProviderError, RateLimitError)
- **Required by**: test runner (`runner/`), which will consume the `AsyncIterator[TokenTiming]` output
- **Dependencies used**: `openai>=1.0.0` (AsyncOpenAI client)
- **No breaking changes** — this is a new module, existing code is unchanged
