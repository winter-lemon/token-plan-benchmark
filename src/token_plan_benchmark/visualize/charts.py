"""Chart generation using matplotlib for benchmark result visualization."""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for headless environments

import matplotlib.pyplot as plt
import seaborn as sns

from token_plan_benchmark.core.models import BenchmarkRun

__all__ = ["generate_tps_chart", "generate_ttft_chart"]

sns.set_theme(style="whitegrid")


def generate_ttft_chart(benchmark_run: BenchmarkRun, output_path: str | Path) -> Path:
    """Generate a TTFT comparison bar chart grouped by provider and model.

    Parameters
    ----------
    benchmark_run:
        The completed benchmark run.
    output_path:
        Path to write the PNG file.

    Returns
    -------
    Path
        Resolved path of the saved chart.
    """
    output_path = Path(output_path)

    # Collect data
    labels: list[str] = []
    ttft_p50: list[float] = []
    ttft_p95: list[float] = []

    for case in benchmark_run.case_results:
        if case.aggregated is None:
            continue
        label = f"{case.provider_name}\n{case.model_id}\n{case.test_case_id}"
        labels.append(label)
        ttft_p50.append(case.aggregated.ttft_p50_ms)
        ttft_p95.append(case.aggregated.ttft_p95_ms)

    if not labels:
        return output_path

    fig, ax = plt.subplots(figsize=(12, 6))
    x = range(len(labels))
    width = 0.35

    bars1 = ax.bar([i - width / 2 for i in x], ttft_p50, width, label="TTFT p50 (ms)", color="#4C72B0")
    bars2 = ax.bar([i + width / 2 for i in x], ttft_p95, width, label="TTFT p95 (ms)", color="#DD8452")

    ax.set_ylabel("Time (ms)")
    ax.set_title(f"TTFT Comparison — {benchmark_run.description or benchmark_run.dimension}")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
    ax.legend()
    ax.bar_label(bars1, fmt="%.0f", fontsize=7, padding=2)
    ax.bar_label(bars2, fmt="%.0f", fontsize=7, padding=2)

    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)

    return output_path.resolve()


def generate_tps_chart(benchmark_run: BenchmarkRun, output_path: str | Path) -> Path:
    """Generate a TPS comparison bar chart grouped by provider and model.

    Parameters
    ----------
    benchmark_run:
        The completed benchmark run.
    output_path:
        Path to write the PNG file.

    Returns
    -------
    Path
        Resolved path of the saved chart.
    """
    output_path = Path(output_path)

    labels: list[str] = []
    tps_p50: list[float] = []

    for case in benchmark_run.case_results:
        if case.aggregated is None:
            continue
        label = f"{case.provider_name}\n{case.model_id}\n{case.test_case_id}"
        labels.append(label)
        tps_p50.append(case.aggregated.tps_p50)

    if not labels:
        return output_path

    fig, ax = plt.subplots(figsize=(12, 6))
    colors = sns.color_palette("viridis", len(labels))
    bars = ax.bar(labels, tps_p50, color=colors)

    ax.set_ylabel("Tokens per second")
    ax.set_title(f"TPS Comparison — {benchmark_run.description or benchmark_run.dimension}")
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
    ax.bar_label(bars, fmt="%.1f", fontsize=8, padding=2)

    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)

    return output_path.resolve()
