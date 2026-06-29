## Context

The project already has core data models (`models.py`), configuration loading (`config.py`), and provider adapters (`providers/adapter.py`). Six modules remain as stubs: CLI, runner, metrics, reporter, storage, visualization. They form a linear pipeline: CLI parses user input → Runner executes benchmarks → Metrics computes stats → Reporter/Storage/Visualization output results.

All providers use async streaming (via `generate_stream`), so the runner must be async. Dependencies (Click, Rich, matplotlib, seaborn) are already declared in `pyproject.toml`.

## Goals / Non-Goals

**Goals:**
- Functional `token-benchmark run` CLI command that loads config and executes a full benchmark
- Sequential execution of test matrix entries with warmup + benchmark iterations
- Statistical aggregation: mean, p50, p95, p99, min, max for TTFT and TPS
- Rich console table output summarizing results grouped by dimension
- JSON persistence of full `BenchmarkRun` to `results/` directory
- matplotlib chart generation: TTFT comparison bar chart, TPS comparison bar chart

**Non-Goals:**
- Concurrent/parallel test execution (v1 is sequential with configurable concurrency)
- CSV/Parquet export (JSON only for v1)
- Interactive visualization (static PNG only)
- Live progress bars during streaming (printed summary at end)

## Decisions

### 1. Async runner with sequential matrix iteration
**Decision**: `async def` runner that iterates the matrix sequentially, calling `generate_stream` for each entry.
**Rationale**: Sequential avoids rate-limiting and is simpler to debug. The runner already has a `cooldown_seconds` parameter for spacing requests. Parallel execution can be added later.

### 2. CLI: single `run` command with `--config` option
**Decision**: One Click command `run` that loads YAML config and starts the benchmark. Optional `--dimension` flag to filter.
**Rationale**: Minimal surface area. The YAML config files already define the full test matrix — no need for many CLI flags.

### 3. Metrics: pure functions over numpy
**Decision**: Compute percentiles manually with `statistics.quantiles()` from stdlib.
**Rationale**: Avoids a numpy dependency. The dataset is small (10 iterations per combo) so stdlib is sufficient.

### 4. Storage: single JSON file per run
**Decision**: Serialize `BenchmarkRun` to `results/<run_id>.json` using dataclass fields.
**Rationale**: JSON is human-readable and loadable by visualization. `dataclasses.asdict()` simplifies serialization.

### 5. Visualization: two chart files
**Decision**: Generate two standalone PNG charts: `results/<run_id>_ttft.png` and `results/<run_id>_tps.png`.
**Rationale**: Separate files are easier to embed in reports. Bar charts with grouped providers are the clearest comparison format.

### 6. Reporter formatting
**Decision**: Use `rich.table.Table` with columns: Provider, Model, Test Case, TTFT (ms) p50/p95, TPS p50/p95.
**Rationale**: Rich provides colored, aligned console output out of the box. Percentiles p50 and p95 give a concise performance summary.

## Risks / Trade-offs

- **Sequential execution is slow**: A full matrix (3 providers × 12 models × 4 test cases × 10 iterations = 1440 calls) takes a while. → Mitigation: show progress after each entry; the real bottleneck is API latency, not local code.
- **JSON serialization of UUID/datetime**: `dataclasses.asdict` doesn't handle UUIDs natively. → Mitigation: use `default=str` with `json.dumps`, or convert to string manually.
- **matplotlib non-interactive backend**: Headless environments may need `matplotlib.use('Agg')`. → Mitigation: set `Agg` backend before importing pyplot.
- **No incremental save**: If the run crashes mid-way, all results are lost. → Mitigation: acceptable for v1; future iteration can add checkpoint saves.
