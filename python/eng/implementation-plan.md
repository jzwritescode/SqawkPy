# SqawkPy Engineering Implementation Plan

This document details the engineering specifications, architectural decisions, and phased implementation roadmap for porting .NET Polly v8 (`Polly.Core`) to Python (`SqawkPy`).

---

## 1. Architecture & Core Design Principles

SqawkPy is a Python resilience and transient-fault-handling library. It models resilience policies through composable pipeline architectures supporting both synchronous and asynchronous execution.

### Architectural Diagram

```
+-----------------------------------------------------------------------+
|                           User Application                            |
|       (Sync: pipeline.execute(...) / Async: await pipeline.execute_async(...)) |
+-----------------------------------------------------------------------+
                                    |
                                    v
+-----------------------------------------------------------------------+
|                          ResiliencePipeline                           |
|  - Leases ResilienceContext from ResilienceContextPool                |
|  - Executes composed pipeline components in configured order          |
|  - Guarantees return of context to pool in finally block              |
+-----------------------------------------------------------------------+
                                    |
         +--------------------------+--------------------------+
         |                          |                          |
         v                          v                          v
+------------------+      +------------------+      +------------------+
| Timeout Strategy | ---> |  Retry Strategy  | ---> | Circuit Breaker  | ---> Target
+------------------+      +------------------+      +------------------+      Operation
         ^                          ^                          ^
         |                          |                          |
+-----------------------------------------------------------------------+
|                      TimeProvider Abstraction                         |
|   (SystemTimeProvider for production, FakeTimeProvider for testing)   |
+-----------------------------------------------------------------------+
```

### Core Design Rules

1. **Return Outcomes, Don't Throw:**
   Strategies communicate failures and results by returning an `Outcome[TResult]` (e.g., `Outcome.from_exception(exc)` or `Outcome.from_result(val)`) from core execution. Exceptions raised by user callbacks must be caught and encapsulated within an `Outcome`, never allowed to escape unexpectedly through strategy middleware.
2. **Dual Synchronous & Asynchronous Execution:**
   Python cannot safely await coroutines synchronously inside an active event loop without risk of deadlocks. SqawkPy provides dual first-class entry points: `execute(...)` for synchronous functions and `execute_async(...)` for coroutines.
3. **Deterministic Time (`TimeProvider`):**
   Strategies never call `time.time()`, `time.monotonic()`, `time.sleep()`, or `asyncio.sleep()` directly. All time checks, timestamps, and delays flow through `TimeProvider`. In tests, `FakeTimeProvider` allows instant simulation of hours of delays without wall-clock sleeps or thread races.
4. **Low-Allocation & Cache Efficiency:**
   Because Python lacks value-type stack-allocated structs, all core execution types (`Outcome`, `ResilienceContext`, arguments classes) utilize `__slots__` to eliminate per-instance `__dict__` overhead (saving ~60% memory and speeding up attribute access). `ResilienceContextPool` recycles contexts to minimize garbage collection pressure on hot execution paths.
5. **Thread and Task Safety:**
   Resilience pipelines are built once and shared across multiple threads and async tasks. Strategies must be stateless with respect to individual executions; per-execution state lives strictly in local variables or on the `ResilienceContext`. Shared stateful components (such as circuit breaker controllers) must synchronize state mutations.

---

## 2. Component Mapping (.NET Polly $\to$ Python SqawkPy)

| .NET Polly (`Polly.Core`) | SqawkPy Module (`python/src/sqawk/`) | Description | Status |
| :--- | :--- | :--- | :--- |
| `Outcome<T>`, `VoidResult` | `sqawk.outcome` | Encapsulates operation results or exceptions. Uses `__slots__`. | **Completed** |
| `ResilienceContext`, `ResilienceProperties`, `ResiliencePropertyKey<T>` | `sqawk.context` | Context flowing through pipeline with typed property bag. | **Completed** |
| `ResilienceContextPool` | `sqawk.context` | Thread-safe object pool recycling `ResilienceContext` instances. | **Completed** |
| `System.TimeProvider`, `FakeTimeProvider` | `sqawk.time_provider` | High-resolution clock & delay abstraction for deterministic testing. | **Completed** |
| `PredicateBuilder`, `OutcomePredicate` | `sqawk.predicates` | Fluent predicate builder matching exceptions and results. | Phase 1 |
| `ResilienceStrategy`, `ResilienceStrategy<T>` | `sqawk.strategy` | Base strategy class defining `execute_core` and `execute_core_async`. | Phase 1 |
| `ResiliencePipeline`, `ResiliencePipelineBuilder` | `sqawk.pipeline` | Fluent composition engine and execution pipeline. | Phase 1 |
| `TimeoutResilienceStrategy` | `sqawk.strategies.timeout` | Enforces execution deadlines and cooperative cancellation. | Phase 2 |
| `RateLimiterResilienceStrategy` | `sqawk.strategies.rate_limiter` | Rate limiting and concurrency throttling. | Phase 2 |
| `RetryResilienceStrategy` | `sqawk.strategies.retry` | Configurable backoff (constant, linear, exponential) & jitter. | Phase 3 |
| `CircuitBreakerResilienceStrategy` | `sqawk.strategies.circuit_breaker` | State machine (`Closed` $\to$ `Open` $\to$ `HalfOpen`) with rolling metrics. | Phase 3 |
| `FallbackResilienceStrategy` | `sqawk.strategies.fallback` | Provides alternative value or action upon failure. | Phase 3 |
| `HedgingResilienceStrategy` | `sqawk.strategies.hedging` | Fires concurrent speculative attempts, returning fastest success. | Phase 3 |
| `ResilienceStrategyTelemetry`, `ResilienceEvent` | `sqawk.telemetry` | Telemetry events, logging, and metrics hooks. | Phase 4 |
| `ResiliencePipelineRegistry` | `sqawk.registry` | Registry for storing, retrieving, and dynamically reloading pipelines. | Phase 5 |

---

## 3. Phased Implementation Roadmap

### Phase 1: Pipeline Core & Execution Engine
* **Deliverables:**
  - `sqawk.predicates.PredicateBuilder`:
    - Fluent predicate chaining: `.handle(ExceptionClass)`, `.handle_result(callable)`, `.handle_if(callable)`.
  - `sqawk.strategy.ResilienceStrategy`:
    - Base class implementing strategy execution pipeline.
  - `sqawk.pipeline.ResiliencePipeline`:
    - `execute(callback, *args, **kwargs)`
    - `execute_async(callback, *args, **kwargs)`
    - `execute_outcome(callback, *args, **kwargs)`
  - `sqawk.pipeline.ResiliencePipelineBuilder`:
    - Builder API: `add_strategy(strategy)`, `add_pipeline(pipeline)`, `build()`.
* **Testing:**
  - `python/test/test_predicate_builder.py` (mirrors `PredicateBuilderTests.cs`).
  - `python/test/test_resilience_pipeline.py` (mirrors `ResiliencePipelineTests.cs`).
  - `python/test/test_pipeline_builder.py` (mirrors `ResiliencePipelineBuilderTests.cs`).

### Phase 2: Proactive Strategies (Timeout & Rate Limiter)
* **Deliverables:**
  - `sqawk.strategies.timeout`:
    - `TimeoutStrategyOptions`: `timeout`, `timeout_generator`, `on_timeout`.
    - `TimeoutRejectedException`.
    - Async deadline enforcement via cooperative cancellation and `asyncio.wait_for`.
  - `sqawk.strategies.rate_limiter`:
    - `RateLimiterStrategyOptions`: token bucket, sliding window, and concurrency limiters.
    - `RateLimitRejectedException`.
* **Testing:**
  - `python/test/test_timeout.py` (mirrors `TimeoutResilienceStrategyTests.cs`).
  - `python/test/test_rate_limiter.py` (mirrors `RateLimiterResilienceStrategyTests.cs`).

### Phase 3: Reactive Strategies (Retry, Circuit Breaker, Fallback, Hedging)
* **Deliverables:**
  - `sqawk.strategies.retry`:
    - Backoff algorithms: `constant`, `linear`, `exponential`.
    - Decorrelated jitter calculation: `RetryHelper.get_retry_delay(...)`.
    - `RetryStrategyOptions`, `OnRetryArguments`, `RetryResilienceStrategy`.
  - `sqawk.strategies.circuit_breaker`:
    - State machine controller: `Closed` $\to$ `Open` $\to$ `HalfOpen`.
    - Two metrics implementations: consecutive failures count and sliding-window rolling metrics (`failure_rate`, `sampling_duration`, `minimum_throughput`).
    - Manual controls: `isolate()` and `reset()`.
    - `BrokenCircuitException`, `IsolatedCircuitException`.
  - `sqawk.strategies.fallback`:
    - `FallbackStrategyOptions`: `should_handle`, `fallback_action`, `on_fallback`.
  - `sqawk.strategies.hedging`:
    - Parallel speculative attempts (`asyncio.create_task`), fastest success resolution.
* **Testing:**
  - `python/test/test_retry.py` (mirrors `RetryResilienceStrategyTests.cs`).
  - `python/test/test_circuit_breaker.py` (mirrors `CircuitBreakerTests.cs`).
  - `python/test/test_fallback.py` (mirrors `FallbackResilienceStrategyTests.cs`).
  - `python/test/test_hedging.py` (mirrors `HedgingResilienceStrategyTests.cs`).
  - `hypothesis` property-based tests verifying backoff ranges, jitter bounds, and state invariants.

### Phase 4: Telemetry & Observability
* **Deliverables:**
  - `sqawk.telemetry.ResilienceStrategyTelemetry`:
    - Structured telemetry events: `OnRetry`, `OnTimeout`, `OnCircuitOpened`, `OnCircuitHalfOpened`, `OnCircuitClosed`, `OnFallback`, `OnHedging`.
    - Logging adapters and OpenTelemetry metrics/tracing listeners.
* **Testing:**
  - `python/test/test_telemetry.py` (mirrors `ResilienceStrategyTelemetryTests.cs`).

### Phase 5: Pipeline Registry & Dynamic Reloading
* **Deliverables:**
  - `sqawk.registry.ResiliencePipelineRegistry`:
    - Named pipeline registration and retrieval.
    - Dynamic reloading (updating strategies without breaking in-flight executions).
    - Lifecycle management and resource disposal.
* **Testing:**
  - `python/test/test_registry.py` (mirrors `ResiliencePipelineRegistryTests.cs`).

### Phase 6: Benchmarks, Hardening & CI/CD
* **Deliverables:**
  - Performance benchmarks in `python/bench/` using `pytest-benchmark`.
  - Mutation testing with `mutmut` to ensure test assertions kill behavioral mutants.
  - GitHub Actions CI workflow (linting, strict type checks, test matrix on Python 3.10-3.13 across Linux/macOS/Windows).

---

## 4. Test Suite Mapping & Deterministic Testing

Every test project in `dotnet/test/Polly.Core.Tests` maps directly to a pytest suite in `python/test/`:

| .NET Test Suite (`dotnet/test/Polly.Core.Tests/`) | Python Pytest Suite (`python/test/`) | Key Focus |
| :--- | :--- | :--- |
| `OutcomeTests.cs` | `test_outcome.py` | Result and exception encapsulation, void semantics, rethrowing. |
| `ResilienceContextTests.cs`, `ResiliencePropertiesTests.cs` | `test_resilience_context.py` | Context initialization, property bags, pool recycling. |
| `TimeProviderExtensionsTests.cs` | `test_time_provider.py` | Virtual time advancement, delay recording, non-blocking time. |
| `PredicateBuilderTests.cs` | `test_predicate_builder.py` | Exception filtering, result predicates, composite rules. |
| `ResiliencePipelineTests.cs` | `test_resilience_pipeline.py` | Sync & async execution, context forwarding, outcome handling. |
| `RetryResilienceStrategyTests.cs` | `test_retry.py` | Attempt counts, backoff progression, jitter calculations, telemetry. |
| `CircuitBreakerTests.cs` | `test_circuit_breaker.py` | State transitions, trip conditions, half-open trials, manual isolation. |
| `TimeoutResilienceStrategyTests.cs` | `test_timeout.py` | Timeout enforcement, cooperative cancellation, timeout generator. |

### Determinism Mandate
- **No real sleeping:** Tests must never call `time.sleep()` or `asyncio.sleep()`. All delays must be executed through `FakeTimeProvider`.
- **Sync and Async Parity:** Every strategy test must verify both synchronous (`def`) and asynchronous (`async def`) execution paths.
- **Coverage Requirement:** $\ge 95\%$ test coverage across all strategy modules.

---

## 5. Engineering Commands

```bash
# Run all unit tests
pytest python/test

# Run tests with coverage reporting
pytest python/test --cov=sqawk --cov-report=term-missing

# Run a specific test suite
pytest python/test/test_outcome.py

# Run property-based tests
pytest python/test -m hypothesis

# Type checking (strict mode)
mypy python/src python/test

# Code formatting and linting
ruff check python
ruff format --check python

# Run performance benchmarks
pytest python/bench --benchmark-only
```

