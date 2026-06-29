# Configuration

## Purpose
Load and validate benchmark configuration from YAML files, build the test matrix, and expose typed access to provider/model/test-case definitions.

## Behavior

### YAML Sources
Four YAML files drive configuration:
1. **`config/providers.yaml`** — list of provider definitions (aliyun, tencent, volcano)
2. **`config/models.yaml`** — model definitions keyed by provider, covering two dimensions:
   - Same model across providers (e.g., deepseek-v3 on all three)
   - Same provider with different models (e.g., qwen-max/plus/turbo on aliyun)
3. **`config/test_cases.yaml`** — benchmark prompts categorized by length
4. **Benchmark run config** — runtime parameters (iterations, concurrency, dimension)

### `BenchmarkConfig` (Pydantic BaseModel)
- `dimension`: BenchmarkDimension enum (default CUSTOM)
- `warmup_iterations`: 0–20 (default 2)
- `benchmark_iterations`: 1–100 (default 10)
- `max_concurrency`: >= 1 (default 1)
- `cooldown_seconds`: >= 0 (default 1.0)
- `providers`, `models`, `test_cases`: string lists for cartesian product
- `test_matrix`: explicit list of {provider, model, test_case} entries (overrides cartesian product)
- Internal lookups: `_provider_configs`, `_model_configs`, `_test_case_defs`

### Test Matrix Building (`build_test_matrix`)
- If `test_matrix` is populated, resolves referenced provider/model/test_case names directly
- Otherwise, computes the cartesian product of `providers × models × test_cases`, filtering out missing provider+model combos

### Configuration Loading (`from_yaml_files`)
- Takes 4 `Path` objects, parses each YAML, populates internal lookup maps
- Returns a fully hydrated `BenchmarkConfig` instance

### Helper Methods
- `get_provider(name) → ProviderConfig`
- `get_model(provider, model_id) → ModelConfig`
- `get_matrix_summary() → str`: human-readable report of all test entries

## Constraints
- Missing YAML files silently yield empty defaults (no error)
- Unknown provider/model references raise `KeyError`

## Implementation
- File: `src/token_plan_benchmark/core/config.py`
