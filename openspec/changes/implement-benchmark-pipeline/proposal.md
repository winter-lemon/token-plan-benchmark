## Why

The benchmark project currently has core models, config loading, and provider adapters, but no runnable pipeline. Without the CLI, runner, metrics, reporter, storage, and visualization modules, the project cannot execute a single benchmark. This change delivers the complete end-to-end pipeline so the project is usable.

## What Changes

- Implement `cli/main.py` with Click-based `token-benchmark` CLI (commands: `run`)
- Implement `runner/` benchmark engine: iterates the test matrix, calls provider adapters, collects results
- Implement `metrics/` statistical computation: percentiles (p50/p95/p99), mean/min/max for TTFT and TPS
- Implement `reporter/` console output with Rich tables summarizing results
- Implement `storage/` JSON-based persistence for `BenchmarkRun` under `results/`
- Implement `visualize/` matplotlib chart generation: TTFT boxplots, TPS bar charts by dimension
- Update `benchmark-pipeline` spec status from planned to implemented

## Capabilities

### New Capabilities
<!-- No new capabilities — all modules are already described in the existing benchmark-pipeline spec -->

### Modified Capabilities
- `benchmark-pipeline`: All six planned modules (cli, runner, metrics, reporter, storage, visualization) transition from planned to implemented. The spec.md status checklist is updated to reflect completion.

## Impact

- **New files**: `cli/main.py`, `runner/engine.py`, `metrics/stats.py`, `reporter/console.py`, `storage/json_store.py`, `visualize/charts.py`
- **Modified files**: `cli/__init__.py`, `runner/__init__.py`, `metrics/__init__.py`, `reporter/__init__.py`, `storage/__init__.py`, `visualize/__init__.py`
- **Entry point**: `token-benchmark` console script becomes functional
- **Dependencies used**: Click, Rich, matplotlib, seaborn (already in pyproject.toml)
- **Data flow**: CLI → Runner → Provider + Metrics → Reporter / Storage / Visualization
