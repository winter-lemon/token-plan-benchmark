# Benchmark Pipeline

## Purpose
Orchestrate end-to-end LLM inference benchmarking: CLI interface, provider adapters, test runner with warmup, metrics computation, result storage, reporting, and visualization.

## Module Architecture

```
cli/         — Click-based command-line entry point (token-benchmark)
providers/   — OpenAI-compatible API client adapters per provider
runner/      — Execution engine: warmup runs, benchmark runs, cooldown
metrics/     — Statistical computation (percentiles, aggregation)
reporter/    — Text/table output via Rich
storage/     — Persistence layer (JSON/Parquet for results)
visualize/   — Charts (matplotlib, seaborn, optional plotly)
```

## Planned Behavior

### CLI (`cli/`)
- Entry point: `token-benchmark` console script
- Commands: `run`, `list-models`, `list-providers`, `show-config`

### Provider Adapters (`providers/`)
- Each provider maps to an OpenAI-compatible endpoint
- Unified interface: `generate_stream(prompt, model, **kwargs) → AsyncIterator[TokenTiming]`
- Handles API key from environment variables

### Runner (`runner/`)
- For each (provider, model, test_case) combination:
  1. Execute warmup iterations (excluded from stats)
  2. Wait cooldown seconds between calls
  3. Execute benchmark iterations (collected for stats)
- Supports configurable concurrency

### Metrics (`metrics/`)
- Compute `AggregatedStats` from a list of `IterationResult`
- Functions: `compute_stats(iterations) → AggregatedStats`
- Percentile calculation: p50, p95, p99

### Reporter (`reporter/`)
- Generate Rich-formatted tables summarizing benchmark results
- Support export formats: console table, CSV, JSON

### Storage (`storage/`)
- Save `BenchmarkRun` to disk (JSON with UUID-based filenames)
- Load historical runs for comparison
- Directory: `results/`

### Visualization (`visualize/`)
- Generate comparison charts: TTFT boxplots, TPS bar charts, latency distributions
- Group by dimension (same model across providers, same provider across models)
- Output: PNG/SVG to `results/` directory

## Constraints
- All providers use the same OpenAI-compatible API pattern (`generic_openai_compat`)
- Streaming mode only (token-by-token timing)
- Benchmark runs are stored under `results/` (git-ignored)
- API keys are read from environment variables only (never from config files)

## Status
- [x] Core data models (models.py, exceptions.py)
- [x] Configuration loading (config.py)
- [ ] CLI
- [ ] Provider adapters
- [ ] Test runner
- [ ] Metrics computation
- [ ] Reporter
- [ ] Storage
- [ ] Visualization
