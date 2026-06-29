"""Statistical aggregation for benchmark iteration results."""

from __future__ import annotations

import statistics
from typing import Sequence

from token_plan_benchmark.core.models import AggregatedStats, IterationResult

__all__ = ["compute_stats"]


def _percentile(values: list[float], pct: float) -> float:
    """Compute the p-th percentile using linear interpolation."""
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    k = (len(sorted_vals) - 1) * (pct / 100.0)
    f = int(k)
    c = f + 1
    if c >= len(sorted_vals):
        return sorted_vals[-1]
    d0 = sorted_vals[f] * (c - k)
    d1 = sorted_vals[c] * (k - f)
    return d0 + d1


def compute_stats(iterations: Sequence[IterationResult]) -> AggregatedStats:
    """Compute aggregated statistics from a list of iteration results.

    Parameters
    ----------
    iterations:
        Benchmark iteration results (warmup iterations should be excluded).

    Returns
    -------
    AggregatedStats
        Mean, percentiles, min, max for TTFT and TPS.
    """
    if not iterations:
        return AggregatedStats(
            count=0,
            ttft_mean_ms=0.0,
            ttft_p50_ms=0.0,
            ttft_p95_ms=0.0,
            ttft_p99_ms=0.0,
            ttft_min_ms=0.0,
            ttft_max_ms=0.0,
            tps_mean=0.0,
            tps_p50=0.0,
            tps_p95=0.0,
            tps_p99=0.0,
            tps_min=0.0,
            tps_max=0.0,
            total_time_mean_ms=0.0,
            total_token_count_mean=0.0,
        )

    ttfts = [r.ttft_ms for r in iterations]
    tpss = [r.tokens_per_second for r in iterations]
    total_times = [r.total_time_ms for r in iterations]
    token_counts = [r.token_count for r in iterations]

    return AggregatedStats(
        count=len(iterations),
        ttft_mean_ms=statistics.mean(ttfts),
        ttft_p50_ms=_percentile(ttfts, 50),
        ttft_p95_ms=_percentile(ttfts, 95),
        ttft_p99_ms=_percentile(ttfts, 99),
        ttft_min_ms=min(ttfts),
        ttft_max_ms=max(ttfts),
        tps_mean=statistics.mean(tpss),
        tps_p50=_percentile(tpss, 50),
        tps_p95=_percentile(tpss, 95),
        tps_p99=_percentile(tpss, 99),
        tps_min=min(tpss),
        tps_max=max(tpss),
        total_time_mean_ms=statistics.mean(total_times),
        total_token_count_mean=statistics.mean(token_counts),
    )
