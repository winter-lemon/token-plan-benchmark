## 1. Metrics module

- [x] 1.1 Create `src/token_plan_benchmark/metrics/stats.py` with `compute_stats(iterations) → AggregatedStats`
- [x] 1.2 Update `src/token_plan_benchmark/metrics/__init__.py` to export `compute_stats`

## 2. Runner module

- [x] 2.1 Create `src/token_plan_benchmark/runner/engine.py` with `BenchmarkRunner` class
- [x] 2.2 Implement `run()` — iterates test matrix, executes warmup + benchmark iterations, collects results into `BenchmarkRun`
- [x] 2.3 Handle errors: record errors on `IterationResult.error`, continue to next entry
- [x] 2.4 Update `src/token_plan_benchmark/runner/__init__.py` to export `BenchmarkRunner`

## 3. Storage module

- [x] 3.1 Create `src/token_plan_benchmark/storage/json_store.py` with `save_run(benchmark_run, dir_path)` and `load_run(run_id, dir_path)`
- [x] 3.2 Handle UUID/datetime serialization via `default=str`
- [x] 3.3 Update `src/token_plan_benchmark/storage/__init__.py` to export `save_run`, `load_run`

## 4. Reporter module

- [x] 4.1 Create `src/token_plan_benchmark/reporter/console.py` with Rich table output
- [x] 4.2 Implement `print_summary(benchmark_run)` — table with provider, model, test case, TTFT p50/p95, TPS p50/p95
- [x] 4.3 Update `src/token_plan_benchmark/reporter/__init__.py` to export `print_summary`

## 5. Visualization module

- [x] 5.1 Create `src/token_plan_benchmark/visualize/charts.py` with matplotlib chart generation
- [x] 5.2 Implement `generate_ttft_chart(benchmark_run, output_path)` — bar chart grouped by provider
- [x] 5.3 Implement `generate_tps_chart(benchmark_run, output_path)` — bar chart grouped by provider
- [x] 5.4 Set non-interactive backend (`matplotlib.use('Agg')`) for headless environments
- [x] 5.5 Update `src/token_plan_benchmark/visualize/__init__.py` to export chart functions

## 6. CLI module

- [x] 6.1 Create `src/token_plan_benchmark/cli/main.py` with Click group and `run` command
- [x] 6.2 `run` command loads YAML config, builds matrix, invokes runner + reporter + storage + visualization
- [x] 6.3 Support `--config-dir` option to specify config directory (default: `config/`)
- [x] 6.4 Update `src/token_plan_benchmark/cli/__init__.py` to export `main`

## 7. Integration verification

- [x] 7.1 Verify `pip install -e ".[dev]"` succeeds
- [x] 7.2 Verify `token-benchmark --help` shows CLI
- [x] 7.3 Verify all pytest tests pass
