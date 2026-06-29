"""Console reporter using Rich for formatted benchmark output."""

from __future__ import annotations

from rich.console import Console
from rich.table import Table

from token_plan_benchmark.core.models import BenchmarkRun

__all__ = ["print_summary"]


def print_summary(benchmark_run: BenchmarkRun) -> None:
    """Print a Rich-formatted summary table of the benchmark results.

    Parameters
    ----------
    benchmark_run:
        The completed benchmark run with aggregated stats.
    """
    console = Console()

    console.print()
    console.print(
        f"[bold]Benchmark Results[/bold] — "
        f"{benchmark_run.description or benchmark_run.dimension}",
    )
    console.print(f"Run ID: [dim]{benchmark_run.run_id}[/dim]")
    console.print()

    table = Table(title="Performance Summary", title_style="bold")

    table.add_column("Provider", style="cyan", no_wrap=True)
    table.add_column("Model", style="green")
    table.add_column("Test Case", style="yellow")
    table.add_column("TTFT p50 (ms)", justify="right")
    table.add_column("TTFT p95 (ms)", justify="right")
    table.add_column("TPS p50", justify="right")
    table.add_column("TPS p95", justify="right")
    table.add_column("Iterations", justify="right")

    for case in benchmark_run.case_results:
        stats = case.aggregated
        if stats is None:
            table.add_row(
                case.provider_name,
                case.model_id,
                case.test_case_id,
                "—",
                "—",
                "—",
                "—",
                str(len(case.benchmark_iterations)),
                style="dim",
            )
            continue

        table.add_row(
            case.provider_name,
            case.model_id,
            case.test_case_id,
            f"{stats.ttft_p50_ms:.1f}",
            f"{stats.ttft_p95_ms:.1f}",
            f"{stats.tps_p50:.1f}",
            f"{stats.tps_p95:.1f}",
            str(stats.count),
        )

    console.print(table)
    console.print()

    # Show errors if any
    errors = [
        (cr.provider_name, cr.model_id, cr.test_case_id, it.error)
        for cr in benchmark_run.case_results
        for it in cr.benchmark_iterations
        if it.error
    ]
    if errors:
        console.print("[bold red]Errors:[/bold red]")
        for provider, model, tc, err in errors:
            console.print(f"  [{provider}/{model}/{tc}] {err}")
