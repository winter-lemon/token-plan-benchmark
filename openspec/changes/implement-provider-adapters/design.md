## Context

The benchmark system measures LLM token generation performance (TTFT, TPS) across three cloud providers. All providers expose OpenAI-compatible `/v1/chat/completions` endpoints with streaming support. We already have `ProviderConfig`, `ModelConfig`, `TestCase`, and `TokenTiming` data models defined in `core/models.py`. The `openai` SDK's `AsyncOpenAI` client is the natural choice for these endpoints.

The design challenge is building a single adapter class that works across all three providers, differing only in `base_url` and API key environment variable.

## Goals / Non-Goals

**Goals:**
- Single `OpenAICompatProvider` class that handles all three providers
- Async streaming interface returning `TokenTiming` records with per-token arrival timestamps
- Accurate TTFT computation using `perf_counter` monotonic clock
- Error classification: rate limits → `RateLimitError`, other API errors → `ProviderError`
- Configurable request timeout per provider
- No provider-specific branching — pure configuration-driven

**Non-Goals:**
- Non-streaming (non-stream) inference — we only need streaming for timing
- Retry logic — the runner layer will handle retries
- Connection pooling or reuse optimization — out of scope for v1
- Direct REST API calls — we use the openai SDK exclusively

## Decisions

### 1. Single adapter vs. per-provider subclass
**Decision**: Single `OpenAICompatProvider` class.
**Rationale**: All three providers use identical API conventions. A single class configured via `ProviderConfig` avoids code duplication. If a provider later diverges (e.g., requires custom auth headers), a subclass or strategy pattern can be introduced without breaking the interface.

**Alternatives considered**: Per-provider subclass (too much boilerplate for identical behavior), strategy pattern (unnecessary abstraction at this stage).

### 2. Async interface with AsyncOpenAI
**Decision**: Use `openai.AsyncOpenAI` client, async generator pattern.
**Rationale**: Async streaming naturally models token-by-token arrival. It allows the runner to process tokens as they arrive (record timestamps, compute TTFT) while the provider is still generating. This matches the `openai` SDK's streaming API: `chat.completions.create(stream=True)` yields chunks.

### 3. TTFT measurement via perf_counter
**Decision**: Use `time.perf_counter()` (monotonic, high-resolution) to capture request start and first token arrival.
**Rationale**: `perf_counter` is unaffected by system clock adjustments and provides nanosecond-level precision on most platforms. First token is detected on the first chunk that has `choice.delta.content` (non-empty text).

### 4. Error mapping
**Decision**: Map HTTP 429 (rate limit) → `RateLimitError`, all other HTTP errors and SDK exceptions → `ProviderError`.
**Rationale**: The runner needs to distinguish rate limits (may retry after cooldown) from other failures (likely fatal for this run). The openai SDK raises `openai.RateLimitError` and `openai.APIStatusError`.

### 5. File structure
**Decision**: Two files: `providers/adapter.py` (the `OpenAICompatProvider` class) and `providers/__init__.py` (re-export).
**Rationale**: Keep it simple. No base class abstraction yet since there's only one adapter type.

## Risks / Trade-offs

- **SDK compatibility**: If a provider's OpenAI-compatible API drifts from the openai SDK's expectations, streaming may break. → Mitigation: The adapter uses only standard `chat.completions.create(stream=True)` params; any drift is caught at runtime with a `ProviderError`.
- **No response validation**: We trust the provider response format. Malformed chunks cause `ProviderError` which the runner handles gracefully. → Mitigation: Add response validation in a future iteration if needed.
- **Timeout**: A stuck connection blocks the entire benchmark pipeline. → Mitigation: `AsyncOpenAI` accepts a `timeout` parameter; we default to 60s, configurable per provider in `ProviderConfig`.
