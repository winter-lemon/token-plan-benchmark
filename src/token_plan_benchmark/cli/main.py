"""CLI entry point for the token benchmark tool."""

from __future__ import annotations

import asyncio
from pathlib import Path

import click

from token_plan_benchmark.core.config import BenchmarkConfig
from token_plan_benchmark.reporter.console import print_summary
from token_plan_benchmark.runner.engine import BenchmarkRunner
from token_plan_benchmark.storage.json_store import save_run
from token_plan_benchmark.visualize.charts import generate_tps_chart, generate_ttft_chart

__all__ = ["main"]


@click.group()
@click.version_option()
def main() -> None:
    """Token Plan Benchmark — Measure LLM token generation performance.

    Benchmarks TTFT (Time to First Token) and TPS (Tokens Per Second)
    across Tencent Hunyuan, Alibaba Bailian, and ByteDance Volcano Engine.
    """


@main.command("run")
@click.option(
    "--config-dir",
    default="config",
    show_default=True,
    type=click.Path(exists=True, file_okay=False),
    help="Directory containing providers.yaml, models.yaml, and test_cases.yaml.",
)
@click.option(
    "--benchmark-config",
    default="benchmark.yaml",
    show_default=True,
    type=click.Path(exists=True, dir_okay=False),
    help="Benchmark run configuration YAML file.",
)
@click.option(
    "--results-dir",
    default="results",
    show_default=True,
    type=click.Path(file_okay=False),
    help="Directory for benchmark output (JSON, charts).",
)
def run_benchmark(config_dir: str, benchmark_config: str, results_dir: str) -> None:
    """Execute a full benchmark run.

    Loads provider, model, and test case configuration from the config
    directory, builds the test matrix, and runs all iterations.
    Results are saved to the results directory.
    """
    config_path = Path(config_dir)
    benchmark_path = Path(benchmark_config)

    click.echo("Loading configuration...")
    config = BenchmarkConfig.from_yaml_files(
        benchmark_path=benchmark_path,
        providers_path=config_path / "providers.yaml",
        models_path=config_path / "models.yaml",
        test_cases_path=config_path / "test_cases.yaml",
    )

    click.echo(config.get_matrix_summary())
    click.echo(f"\nWarmup: {config.warmup_iterations}, "
               f"Benchmark: {config.benchmark_iterations}, "
               f"Cooldown: {config.cooldown_seconds}s\n")

    click.echo("Running benchmark...")
    runner = BenchmarkRunner(config)
    result = asyncio.run(runner.run())

    click.echo("Saving results...")
    json_path = save_run(result, dir_path=results_dir)
    click.echo(f"  JSON: {json_path}")

    click.echo("Generating charts...")
    ttft_path = generate_ttft_chart(result, f"{results_dir}/{result.run_id}_ttft.png")
    tps_path = generate_tps_chart(result, f"{results_dir}/{result.run_id}_tps.png")
    click.echo(f"  TTFT: {ttft_path}")
    click.echo(f"  TPS:  {tps_path}")

    print_summary(result)
    click.echo("Done.")
