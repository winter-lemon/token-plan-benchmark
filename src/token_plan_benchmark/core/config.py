"""Configuration loading and validation using Pydantic."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field

from token_plan_benchmark.core.models import (
    BenchmarkDimension,
    ModelConfig,
    ProviderConfig,
    TestCase,
)


class BenchmarkConfig(BaseModel):
    """Top-level benchmark configuration loaded from YAML files."""

    model_config = {"arbitrary_types_allowed": True}

    dimension: BenchmarkDimension = BenchmarkDimension.CUSTOM
    description: str = ""
    run_name: Optional[str] = None

    warmup_iterations: int = Field(default=2, ge=0, le=20)
    benchmark_iterations: int = Field(default=10, ge=1, le=100)
    max_concurrency: int = Field(default=1, ge=1)
    cooldown_seconds: float = Field(default=1.0, ge=0.0)

    providers: list[str] = Field(default_factory=list)
    models: list[str] = Field(default_factory=list)
    test_cases: list[str] = Field(default_factory=list)

    # Explicit test matrix (overrides cartesian product)
    test_matrix: list[dict] = Field(default_factory=list)

    # Loaded references (populated after load, not from YAML)
    _provider_configs: dict[str, ProviderConfig] = {}
    _model_configs: dict[str, dict[str, ModelConfig]] = {}
    _test_case_defs: dict[str, TestCase] = {}

    def build_test_matrix(self) -> list[dict]:
        """Build the list of (provider, model, test_case) combinations to run."""
        if self.test_matrix:
            entries = []
            for entry in self.test_matrix:
                tc = self._test_case_defs[entry["test_case"]]
                entries.append({
                    "provider": entry["provider"],
                    "model": entry["model"],
                    "test_case": tc,
                })
            return entries

        # Cartesian product
        matrix = []
        for provider in self.providers:
            for model in self.models:
                for tc_id in self.test_cases:
                    tc = self._test_case_defs[tc_id]
                    # Check if this provider+model combo exists in model configs
                    if provider in self._model_configs and model in self._model_configs[provider]:
                        matrix.append({
                            "provider": provider,
                            "model": model,
                            "test_case": tc,
                        })
        return matrix

    def get_provider(self, name: str) -> ProviderConfig:
        if name not in self._provider_configs:
            raise KeyError(f"Unknown provider: {name}")
        return self._provider_configs[name]

    def get_model(self, provider: str, model_id: str) -> ModelConfig:
        if provider not in self._model_configs:
            raise KeyError(f"No models configured for provider: {provider}")
        if model_id not in self._model_configs[provider]:
            raise KeyError(f"Unknown model {model_id} for provider {provider}")
        return self._model_configs[provider][model_id]

    @classmethod
    def from_yaml_files(
        cls,
        benchmark_path: Path,
        providers_path: Path,
        models_path: Path,
        test_cases_path: Path,
    ) -> "BenchmarkConfig":
        """Load configuration from the standard set of YAML files."""
        benchmark_data = _load_yaml(benchmark_path)
        providers_data = _load_yaml(providers_path)
        models_data = _load_yaml(models_path)
        test_cases_data = _load_yaml(test_cases_path)

        config = cls(**benchmark_data)

        # Load provider configs
        config._provider_configs = {}
        for p in providers_data.get("providers", []):
            provider = ProviderConfig(**p)
            config._provider_configs[provider.name] = provider

        # Load model configs (keyed by provider -> model_id)
        config._model_configs = {}
        for m in models_data.get("models", []):
            model = ModelConfig(**m)
            config._model_configs.setdefault(model.provider, {})[model.model_id] = model

        # Load test case definitions
        config._test_case_defs = {}
        for tc in test_cases_data.get("test_cases", []):
            test_case = TestCase(**tc)
            config._test_case_defs[test_case.id] = test_case

        return config

    def get_matrix_summary(self) -> str:
        """Return a human-readable summary of the test matrix."""
        matrix = self.build_test_matrix()
        lines = [
            f"Dimension: {self.dimension.value}",
            f"Description: {self.description or '(none)'}",
            f"Warmup iterations: {self.warmup_iterations}",
            f"Benchmark iterations: {self.benchmark_iterations}",
            f"Total test cases: {len(matrix)}",
            "",
        ]
        for i, entry in enumerate(matrix):
            lines.append(
                f"  [{i+1}] {entry['provider']} / {entry['model']} / {entry['test_case'].name}"
            )
        return "\n".join(lines)


def _load_yaml(path: Path) -> dict:
    """Load a YAML file, returning an empty dict if the file doesn't exist."""
    if not path.exists():
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}
