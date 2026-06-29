"""Custom exceptions for the benchmark system."""


class BenchmarkError(Exception):
    """Base exception for all benchmark errors."""
    pass


class ConfigurationError(BenchmarkError):
    """Raised when configuration is invalid."""
    pass


class ProviderError(BenchmarkError):
    """Raised when a provider API call fails."""
    pass


class RateLimitError(ProviderError):
    """Raised when hitting a provider's rate limit."""
    pass
