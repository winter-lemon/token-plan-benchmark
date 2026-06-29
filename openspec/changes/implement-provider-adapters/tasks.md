## 1. Module setup

- [x] 1.1 Create `src/token_plan_benchmark/providers/adapter.py` with the `OpenAICompatProvider` class skeleton
- [x] 1.2 Update `src/token_plan_benchmark/providers/__init__.py` to export `OpenAICompatProvider`

## 2. Core adapter implementation

- [x] 2.1 Implement `__init__` — create `AsyncOpenAI` client from `ProviderConfig` (`base_url`, `api_key_env`, `extra_headers`, `extra_body`); raise `ConfigurationError` if the environment variable is missing
- [x] 2.2 Implement `generate_stream` — accept `model_id`, `prompt`, optional `system_prompt`; call `chat.completions.create(stream=True)`; yield `TokenTiming` records with `token_index`, `text`, `arrival_time_s`, `inter_token_latency_ms`
- [x] 2.3 Capture TTFT — record `time.perf_counter()` at request start; compute `arrival_time_s` as delta on first content-bearing chunk
- [x] 2.4 Skip empty/whitespace-only chunks — only yield `TokenTiming` when `delta.content` is non-empty
- [x] 2.5 Apply configurable timeout — default 60s, overridable via `ProviderConfig.extra_body["timeout"]`

## 3. Error handling

- [x] 3.1 Map `openai.RateLimitError` (HTTP 429) → `RateLimitError` with the original message
- [x] 3.2 Map `openai.APIStatusError` and other SDK exceptions → `ProviderError` with the original message and status code

## 4. Tests

- [x] 4.1 Create `tests/providers/__init__.py` and `tests/providers/test_adapter.py`
- [x] 4.2 Test: initialization with valid `ProviderConfig` creates `AsyncOpenAI` client
- [x] 4.3 Test: missing API key environment variable raises `ConfigurationError`
- [x] 4.4 Test: `generate_stream` yields correct `TokenTiming` records from mock streaming response
- [x] 4.5 Test: TTFT is measured correctly on first token
- [x] 4.6 Test: empty content chunks are skipped
- [x] 4.7 Test: `RateLimitError` is raised on HTTP 429
- [x] 4.8 Test: `ProviderError` is raised on other HTTP errors
- [x] 4.9 Test: default 60s timeout is applied; custom timeout from config is respected
- [x] 4.10 Verify tests pass with `pytest tests/providers/ -v`
