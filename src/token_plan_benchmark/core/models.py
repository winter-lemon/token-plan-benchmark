"""Core data models for the benchmark system.

All models use dataclasses for simplicity and easy serialization.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4


# ── Enums ────────────────────────────────────────────────────────────


class BenchmarkDimension(str, Enum):
    SAME_MODEL_DIFFERENT_PROVIDER = "same_model_different_provider"
    SAME_PROVIDER_DIFFERENT_MODEL = "same_provider_different_model"
    CUSTOM = "custom"


class RunPhase(str, Enum):
    WARMUP = "warmup"
    BENCHMARK = "benchmark"


# ── Provider & Model Definitions ─────────────────────────────────────


@dataclass
class ProviderConfig:
    """Definition of a single inference provider."""
    name: str
    display_name: str
    adapter: str
    base_url: str
    api_key_env: str
    base_url_env: str = ""
    extra_headers: dict[str, str] = field(default_factory=dict)
    extra_body: dict = field(default_factory=dict)


@dataclass
class ModelConfig:
    """Definition of a model that can be used on one or more providers."""
    model_id: str
    display_name: str
    provider: str
    max_tokens: int = 4096


# ── Test Case Definition ─────────────────────────────────────────────


@dataclass
class TestCase:
    """A single benchmark test case."""
    id: str
    name: str
    prompt: str
    system_prompt: Optional[str] = None
    expected_output_tokens: int = 256
    category: str = "general"


# ── Per-Token Timing ─────────────────────────────────────────────────


@dataclass
class TokenTiming:
    """Timing for a single token in a streaming response."""
    token_index: int
    text: str
    arrival_time_s: float
    inter_token_latency_ms: float


# ── Single Iteration Result ──────────────────────────────────────────


@dataclass
class IterationResult:
    """Result from a single inference call (one iteration)."""
    run_id: UUID
    iteration: int
    phase: RunPhase
    provider_name: str
    model_id: str
    test_case_id: str

    request_start_ts: datetime
    ttft_ms: float
    total_time_ms: float
    token_count: int
    tokens_per_second: float

    token_timings: list[TokenTiming] = field(default_factory=list)
    inter_token_latencies_ms: list[float] = field(default_factory=list)
    finish_reason: str = ""
    error: Optional[str] = None


# ── Aggregated Statistics ────────────────────────────────────────────


@dataclass
class AggregatedStats:
    """Statistical summary across iterations for one (provider, model, test_case)."""
    count: int
    ttft_mean_ms: float
    ttft_p50_ms: float
    ttft_p95_ms: float
    ttft_p99_ms: float
    ttft_min_ms: float
    ttft_max_ms: float

    tps_mean: float
    tps_p50: float
    tps_p95: float
    tps_p99: float
    tps_min: float
    tps_max: float

    total_time_mean_ms: float
    total_token_count_mean: float


# ── Per-Case Result ──────────────────────────────────────────────────


@dataclass
class BenchmarkCaseResult:
    """Aggregated result for one (provider, model, test_case) combination."""
    provider_name: str
    model_id: str
    test_case_id: str
    benchmark_iterations: list[IterationResult] = field(default_factory=list)
    warmup_iterations: list[IterationResult] = field(default_factory=list)
    aggregated: Optional[AggregatedStats] = None


# ── Full Run Result ──────────────────────────────────────────────────


@dataclass
class BenchmarkRun:
    """Top-level container for an entire benchmark run."""
    run_id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    dimension: BenchmarkDimension = BenchmarkDimension.CUSTOM
    description: str = ""
    case_results: list[BenchmarkCaseResult] = field(default_factory=list)
    config_snapshot: dict = field(default_factory=dict)
