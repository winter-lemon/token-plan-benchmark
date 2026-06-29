## ADDED Requirements

### Requirement: Unified provider adapter interface

The system SHALL provide an `OpenAICompatProvider` class that accepts a `ProviderConfig` and exposes an async `generate_stream` method producing `TokenTiming` records for any OpenAI-compatible LLM endpoint.

#### Scenario: Provider initialization from config

- **WHEN** an `OpenAICompatProvider` is initialized with a `ProviderConfig` containing `base_url`, `api_key_env`, and optional `extra_headers`/`extra_body`
- **THEN** an `AsyncOpenAI` client is created with the configured `base_url`, API key from the environment variable, and any extra parameters

#### Scenario: Missing API key raises error

- **WHEN** a provider is initialized and the environment variable specified by `api_key_env` is not set
- **THEN** a `ConfigurationError` is raised with a message naming the missing environment variable

### Requirement: Streaming token generation

The `generate_stream(provider_config, model_config, test_case)` method SHALL send a streaming chat completion request and yield `TokenTiming` records for each content-bearing token chunk received.

#### Scenario: Successful streaming with timing

- **WHEN** `generate_stream` is called with a valid provider config, model config (containing `model_id`), and test case (containing `prompt` and optional `system_prompt`)
- **THEN** the method yields `TokenTiming` records for each token, each containing `token_index` (0-based), `text` (the delta content), `arrival_time_s` (monotonic seconds since request start), and `inter_token_latency_ms` (milliseconds since the previous token, 0.0 for the first token)

#### Scenario: TTFT captured on first token

- **WHEN** the first non-empty content chunk arrives
- **THEN** the first `TokenTiming` record has `arrival_time_s` equal to the time difference between `perf_counter()` at request start and token arrival, and `inter_token_latency_ms` is `0.0`

#### Scenario: Empty content chunks are skipped

- **WHEN** a streaming chunk arrives with `delta.content` that is empty or contains only whitespace
- **THEN** no `TokenTiming` record is yielded for that chunk

#### Scenario: Streaming completes normally

- **WHEN** the provider finishes sending all tokens and the stream closes normally
- **THEN** the async generator exits cleanly without raising an error

### Requirement: Provider error classification

Provider API errors SHALL be mapped to the existing exception hierarchy: HTTP 429 responses SHALL raise `RateLimitError`, and all other HTTP or SDK errors SHALL raise `ProviderError`.

#### Scenario: Rate limit error

- **WHEN** the provider returns an HTTP 429 status code during streaming
- **THEN** a `RateLimitError` is raised with the original error message

#### Scenario: Other API error

- **WHEN** the provider returns any other HTTP error status (e.g., 401, 500) or the SDK raises a non-rate-limit exception
- **THEN** a `ProviderError` is raised with the original error message and status code

### Requirement: Request timeout

Each provider request SHALL respect a configurable timeout to prevent hung connections from blocking the benchmark pipeline.

#### Scenario: Default timeout applied

- **WHEN** `ProviderConfig` does not specify a custom timeout
- **THEN** the `AsyncOpenAI` client is created with a default timeout of 60 seconds

#### Scenario: Custom timeout from config

- **WHEN** `ProviderConfig.extra_body` includes a `timeout` key
- **THEN** the `AsyncOpenAI` client uses that value as the request timeout in seconds
