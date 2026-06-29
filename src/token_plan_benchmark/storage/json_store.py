"""JSON-based persistence for benchmark runs."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from uuid import UUID

from token_plan_benchmark.core.models import BenchmarkRun

__all__ = ["load_run", "save_run"]


class _Encoder(json.JSONEncoder):
    """Custom encoder that handles UUID, datetime, and dataclass types."""

    def default(self, o: object) -> object:
        if isinstance(o, UUID):
            return str(o)
        if isinstance(o, datetime):
            return o.isoformat()
        if is_dataclass(o) and not isinstance(o, type):
            return asdict(o)
        return super().default(o)


def save_run(benchmark_run: BenchmarkRun, dir_path: str | Path = "results") -> Path:
    """Persist a benchmark run to a JSON file.

    Parameters
    ----------
    benchmark_run:
        The completed benchmark run to save.
    dir_path:
        Directory to write the file (created if it doesn't exist).

    Returns
    -------
    Path
        Path to the written file.
    """
    dir_path = Path(dir_path)
    dir_path.mkdir(parents=True, exist_ok=True)

    file_path = dir_path / f"{benchmark_run.run_id}.json"
    data = asdict(benchmark_run)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, cls=_Encoder, indent=2, ensure_ascii=False)

    return file_path


def load_run(run_id: str | UUID, dir_path: str | Path = "results") -> BenchmarkRun:
    """Load a previously saved benchmark run from JSON.

    Parameters
    ----------
    run_id:
        The UUID of the run to load.
    dir_path:
        Directory containing the JSON file.

    Returns
    -------
    BenchmarkRun
        The deserialized benchmark run.

    Raises
    ------
    FileNotFoundError
        If no JSON file exists for the given run_id.
    """
    dir_path = Path(dir_path)
    file_path = dir_path / f"{run_id}.json"

    if not file_path.exists():
        raise FileNotFoundError(f"Benchmark run not found: {file_path}")

    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)

    # Reconstruct from raw dict — UUID/datetime are strings in JSON
    # but dataclass fields accept them for display purposes
    from token_plan_benchmark.core.models import (
        AggregatedStats,
        BenchmarkCaseResult,
        IterationResult,
        RunPhase,
        TokenTiming,
    )

    def _parse_iteration(item: dict) -> IterationResult:
        return IterationResult(
            run_id=UUID(item["run_id"]),
            iteration=item["iteration"],
            phase=RunPhase(item["phase"]),
            provider_name=item["provider_name"],
            model_id=item["model_id"],
            test_case_id=item["test_case_id"],
            request_start_ts=datetime.fromisoformat(item["request_start_ts"]),
            ttft_ms=item["ttft_ms"],
            total_time_ms=item["total_time_ms"],
            token_count=item["token_count"],
            tokens_per_second=item["tokens_per_second"],
            token_timings=[TokenTiming(**t) for t in item.get("token_timings", [])],
            inter_token_latencies_ms=item.get("inter_token_latencies_ms", []),
            finish_reason=item.get("finish_reason", ""),
            error=item.get("error"),
        )

    def _parse_stats(s: dict | None) -> AggregatedStats | None:
        if s is None:
            return None
        return AggregatedStats(**s)

    case_results = []
    for cr in data.get("case_results", []):
        case_results.append(BenchmarkCaseResult(
            provider_name=cr["provider_name"],
            model_id=cr["model_id"],
            test_case_id=cr["test_case_id"],
            benchmark_iterations=[_parse_iteration(i) for i in cr.get("benchmark_iterations", [])],
            warmup_iterations=[_parse_iteration(i) for i in cr.get("warmup_iterations", [])],
            aggregated=_parse_stats(cr.get("aggregated")),
        ))

    return BenchmarkRun(
        run_id=UUID(data["run_id"]),
        timestamp=datetime.fromisoformat(data["timestamp"]),
        dimension=data.get("dimension", "custom"),
        description=data.get("description", ""),
        case_results=case_results,
        config_snapshot=data.get("config_snapshot", {}),
    )
