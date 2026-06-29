## MODIFIED Requirements

### Requirement: CLI command entry point

The system SHALL provide a `token-benchmark` CLI via Click with a `run` subcommand that loads benchmark configuration from the standard YAML files and executes the full pipeline.

#### Scenario: Run with default config paths

- **WHEN** user executes `token-benchmark run`
- **THEN** configuration is loaded from `config/` directory, the test matrix is built, and the benchmark executes sequentially

#### Scenario: Run with custom config directory

- **WHEN** user executes `token-benchmark run --config-dir my-config/`
- **THEN** configuration YAML files are loaded from `my-config/` instead of `config/`

### Requirement: Benchmark runner engine

The runner SHALL iterate the test matrix sequentially, executing warmup and benchmark iterations for each (provider, model, test_case) combination, collecting `IterationResult` objects into a `BenchmarkRun`.

#### Scenario: Full matrix execution

- **WHEN** the runner processes a test matrix with N entries, each configured with W warmup and B benchmark iterations
- **THEN** for each entry, W warmup calls are made (results discarded from aggregation), followed by B benchmark calls (results collected), with `cooldown_seconds` delay between calls

#### Scenario: Error handling during run

- **WHEN** a provider call fails with `ProviderError` or `RateLimitError`
- **THEN** the error is recorded on the `IterationResult.error` field and execution continues with the next entry

### Requirement: Metrics computation

The metrics module SHALL compute `AggregatedStats` from a list of `IterationResult` objects, returning mean, p50, p95, p99, min, and max for both TTFT and TPS.

#### Scenario: Statistical aggregation

- **WHEN** given N benchmark iterations with varying TTFT and TPS values
- **THEN** `AggregatedStats` is returned with `count=N`, correct `ttft_mean_ms`, `ttft_p50_ms`, `ttft_p95_ms`, `ttft_p99_ms`, `ttft_min_ms`, `ttft_max_ms`, and corresponding TPS fields

#### Scenario: Single iteration

- **WHEN** given exactly 1 iteration result
- **THEN** all percentile, mean, min, and max values equal that single iteration's values

### Requirement: Console reporter

The reporter SHALL output a Rich-formatted table summarizing benchmark results with columns for provider, model, test case, warmup TTFT, benchmark TTFT p50/p95, and TPS p50/p95.

#### Scenario: Table output after run

- **WHEN** a `BenchmarkRun` with completed case results is passed to the reporter
- **THEN** a Rich table is printed to stdout with one row per (provider, model, test_case) combination, showing aggregated stats

### Requirement: JSON storage

The storage module SHALL persist a `BenchmarkRun` to a JSON file under `results/<run_id>.json` and support loading historical runs.

#### Scenario: Save benchmark run

- **WHEN** `save_run(benchmark_run)` is called
- **THEN** a JSON file is written to `results/<run_id>.json` containing the full run data with UUIDs and datetimes serialized as strings

#### Scenario: Load historical run

- **WHEN** `load_run(run_id)` is called with an existing run UUID
- **THEN** the `BenchmarkRun` is deserialized from `results/<run_id>.json`

### Requirement: Visualization charts

The visualization module SHALL generate comparison bar charts as PNG files: one for TTFT (grouped by provider) and one for TPS.

#### Scenario: Generate TTFT chart

- **WHEN** a `BenchmarkRun` with multiple case results is passed to the visualization
- **THEN** a PNG bar chart is saved to `results/<run_id>_ttft.png` showing TTFT p50 and p95 grouped by provider and model

#### Scenario: Generate TPS chart

- **WHEN** a `BenchmarkRun` with multiple case results is passed to the visualization
- **THEN** a PNG bar chart is saved to `results/<run_id>_tps.png` showing TPS p50 grouped by provider and model
