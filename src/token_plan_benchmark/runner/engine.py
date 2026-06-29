"""Benchmark execution engine."""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone
from uuid import uuid4

from token_plan_benchmark.core.config import BenchmarkConfig
from token_plan_benchmark.core.exceptions import BenchmarkError
from token_plan_benchmark.core.models import (
    BenchmarkCaseResult,
    BenchmarkRun,
    IterationResult,
    RunPhase,
)
from token_plan_benchmark.metrics.stats import compute_stats
from token_plan_benchmark.providers.adapter import OpenAICompatProvider

__all__ = ["BenchmarkRunner"]


class BenchmarkRunner:
    """Orchestrates a full benchmark run across the test matrix."""

    def __init__(self, config: BenchmarkConfig) -> None:
        self._config = config

    async def run(self) -> BenchmarkRun:
        """Execute the benchmark and return results.

        Iterates the test matrix, running warmup + benchmark iterations
        for each (provider, model, test_case) combination with cooldown
        delays between calls.

        Returns
        -------
        BenchmarkRun
            Complete benchmark run with all case results aggregated.
        """
        run_id = uuid4()
        matrix = self._config.build_test_matrix()
        case_results: list[BenchmarkCaseResult] = []

        for entry in matrix:
            provider_name = entry["provider"]
            model_id = entry["model"]
            test_case = entry["test_case"]

            provider_cfg = self._config.get_provider(provider_name)
            model_cfg = self._config.get_model(provider_name, model_id)
            adapter = OpenAICompatProvider(provider_cfg)

            result = BenchmarkCaseResult(
                provider_name=provider_name,
                model_id=model_id,
                test_case_id=test_case.id,
            )

            # Warmup iterations
            for i in range(self._config.warmup_iterations):
                it = await _run_single(
                    adapter, model_cfg, test_case, run_id, i, RunPhase.WARMUP
                )
                result.warmup_iterations.append(it)
                await asyncio.sleep(self._config.cooldown_seconds)

            # Benchmark iterations
            for i in range(self._config.benchmark_iterations):
                it = await _run_single(
                    adapter, model_cfg, test_case, run_id, i, RunPhase.BENCHMARK
                )
                result.benchmark_iterations.append(it)
                if i < self._config.benchmark_iterations - 1:
                    await asyncio.sleep(self._config.cooldown_seconds)

            # Aggregate stats (from benchmark iterations only)
            valid = [it for it in result.benchmark_iterations if it.error is None]
            if valid:
                result.aggregated = compute_stats(valid)

            case_results.append(result)

            # Cooldown between entries
            await asyncio.sleep(self._config.cooldown_seconds)

        return BenchmarkRun(
            run_id=run_id,
            timestamp=datetime.now(timezone.utc),
            dimension=self._config.dimension,
            description=self._config.description,
            case_results=case_results,
            config_snapshot={
                "dimension": self._config.dimension.value,
                "description": self._config.description,
                "warmup_iterations": self._config.warmup_iterations,
                "benchmark_iterations": self._config.benchmark_iterations,
                "max_concurrency": self._config.max_concurrency,
                "cooldown_seconds": self._config.cooldown_seconds,
            },
        )


async def _run_single(
    adapter: OpenAICompatProvider,
    model_cfg,
    test_case,
    run_id,
    iteration: int,
    phase: RunPhase,
) -> IterationResult:
    """Run a single inference call and produce an IterationResult."""
    request_start_ts = datetime.now(timezone.utc)
    start_time = time.perf_counter()
    tokens = []
    error = None
    finish_reason = ""

    try:
        async for token in adapter.generate_stream(model_cfg, test_case):
            tokens.append(token)
        finish_reason = "stop"
    except BenchmarkError as exc:
        error = str(exc)
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"

    total_time_s = time.perf_counter() - start_time
    token_count = len(tokens)
    ttft_ms = tokens[0].arrival_time_s * 1000.0 if tokens else 0.0
    tps = token_count / total_time_s if total_time_s > 0 else 0.0
    inter_token_latencies = [t.inter_token_latency_ms for t in tokens]

    return IterationResult(
        run_id=run_id,
        iteration=iteration,
        phase=phase,
        provider_name=adapter._config.name,
        model_id=model_cfg.model_id,
        test_case_id=test_case.id,
        request_start_ts=request_start_ts,
        ttft_ms=ttft_ms,
        total_time_ms=total_time_s * 1000.0,
        token_count=token_count,
        tokens_per_second=tps,
        token_timings=tokens,
        inter_token_latencies_ms=inter_token_latencies,
        finish_reason=finish_reason,
        error=error,
    )
