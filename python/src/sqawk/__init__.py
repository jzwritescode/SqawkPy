"""SqawkPy: Resilience and transient-fault-handling library for Python (port of Polly)."""

from sqawk.context import (
    ResilienceContext,
    ResilienceContextPool,
    ResilienceProperties,
    ResiliencePropertyKey,
    SharedResilienceContextPool,
)
from sqawk.outcome import Outcome, VoidResult
from sqawk.time_provider import (
    FakeTimeProvider,
    SystemTime,
    SystemTimeProvider,
    TimeProvider,
)

__all__ = [
    "Outcome",
    "VoidResult",
    "ResilienceContext",
    "ResilienceContextPool",
    "ResilienceProperties",
    "ResiliencePropertyKey",
    "SharedResilienceContextPool",
    "TimeProvider",
    "SystemTimeProvider",
    "FakeTimeProvider",
    "SystemTime",
]

__version__ = "0.1.0"
