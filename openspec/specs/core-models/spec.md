# Core Models

## Purpose
Define all data structures used throughout the benchmark system: provider definitions, model configurations, test cases, timing records, and run results.

## Behavior

### Provider Config (`ProviderConfig`)
- Holds provider metadata: `name`, `display_name`, `adapter`, `base_url`, `api_key_env`
- `adapter` determines how API calls are routed (currently all use `generic_openai_compat`)
- Supports `extra_headers` and `extra_body` for provider-specific request customization

### Model Config (`ModelConfig`)
- Maps a `model_id` to a specific `provider`
- Includes `display_name` and `max_tokens` (default 4096)
- One model can be deployed across multiple providers (e.g., `deepseek-v3` on aliyun, tencent, volcano)

### Test Case (`TestCase`)
- Defines a benchmark prompt with: `id`, `name`, `prompt`, optional `system_prompt`, `expected_output_tokens`, `category`
- Categories: `short`, `medium`, `long`, `code`

### Token Timing (`TokenTiming`)
- Per-token record from streaming responses: `token_index`, `text`, `arrival_time_s`, `inter_token_latency_ms`

### Iteration Result (`IterationResult`)
- Result of a single inference call, containing: `run_id`, `iteration`, `phase` (WARMUP/BENCHMARK), `provider_name`, `model_id`, `test_case_id`
- Timing metrics: `ttft_ms`, `total_time_ms`, `token_count`, `tokens_per_second`
- Optional `token_timings` list and `inter_token_latencies_ms` for detailed analysis

### Aggregated Stats (`AggregatedStats`)
- Statistical summary across iterations: count, percentiles (p50/p95/p99) for TTFT and TPS, min/max for both

### Benchmark Case Result (`BenchmarkCaseResult`)
- Groups results for one (provider, model, test_case) combination
- Separates `benchmark_iterations` from `warmup_iterations`

### Benchmark Run (`BenchmarkRun`)
- Top-level container: `run_id` (UUID), `timestamp`, `dimension`, `description`, list of `case_results`, `config_snapshot`

### Enums
- `BenchmarkDimension`: `SAME_MODEL_DIFFERENT_PROVIDER`, `SAME_PROVIDER_DIFFERENT_MODEL`, `CUSTOM`
- `RunPhase`: `WARMUP`, `BENCHMARK`

## Exceptions
- `BenchmarkError` (base) → `ConfigurationError`, `ProviderError` → `RateLimitError`

## Implementation
- File: `src/token_plan_benchmark/core/models.py`
- File: `src/token_plan_benchmark/core/exceptions.py`
