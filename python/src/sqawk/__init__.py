"""
SqawkPy: Resilience and Transient-Fault-Handling Library for Python.

SqawkPy is a Python port of .NET's Polly resilience library. It allows
developers to express resilience strategies—such as Retry, Circuit Breaker,
Timeout, Rate Limiter, Fallback, and Hedging—through fluent, composable pipelines.

Modules
-------
outcome
    `Outcome[TResult]` and `VoidResult` encapsulation types.
context
    `ResilienceContext`, typed property keys, and thread-safe context pooling.
time_provider
    `TimeProvider`, `SystemTimeProvider`, and `FakeTimeProvider` time abstractions.

Notes
-----
This library supports dual synchronous (`execute`) and asynchronous (`execute_async`)
execution paths with identical resilience behaviors and zero external runtime dependencies.
"""

from __future__ import annotations

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
