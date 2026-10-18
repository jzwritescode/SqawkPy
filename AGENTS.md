# Coding Agent Instructions

This file provides guidance to agents when working with code in this repository.

## Commands

```bash
# Run all tests
pytest python/test

# Run tests with coverage
pytest python/test --cov=sqawk --cov-report=term-missing

# Run a specific test file
pytest python/test/test_outcome.py

# Run a single test by expression
pytest python/test -k "test_circuit_breaker"

# Run property-based tests
pytest python/test -m hypothesis

# Type checking
mypy python/src python/test

# Linting and formatting
ruff check python
ruff format --check python

# Benchmarks
pytest python/bench --benchmark-only
```

Lint runs in CI via GitHub Actions workflows (actionlint, zizmor, ruff).

## Architecture

SqawkPy is a Python port of the .NET Polly resilience library. It models resilience policies through composable pipeline architectures supporting both synchronous and asynchronous execution.

### Core abstractions (`python/src/sqawk`)

- **`ResiliencePipeline`** — the primary execution interface. Wraps one or more strategies and executes them in sequence.
- **`ResiliencePipelineBuilder`** — fluent builder used to compose strategies.
- **`ResilienceStrategy`** — abstract base class for all built-in and custom resilience strategies.
- **`ResilienceContext`** — per-execution context flowing through the pipeline (cancellation tokens, arbitrary properties, result type, etc.).
- **`Outcome[TResult]`** — encapsulates the outcome of an execution (either a successful result value or an exception).
- **`TimeProvider`** — clock and delay abstraction (`SystemTimeProvider` for production, `FakeTimeProvider` for deterministic testing).

### Built-in strategies

Strategies split into two categories:

**Reactive** (respond to failures):

- `RetryResilienceStrategy` — configurable backoff, jitter, attempt limits.
- `CircuitBreakerResilienceStrategy` — state machine: `Closed` → `Open` → `HalfOpen`.
- `FallbackResilienceStrategy` — returns an alternative value/action on failure.
- `HedgingResilienceStrategy` — fires parallel attempts and returns the fastest success.

**Proactive** (prevent overload):

- `TimeoutResilienceStrategy` — bounds execution duration.
- `RateLimiterResilienceStrategy` — controls execution rate.

Each strategy has a corresponding `*Options` dataclass/class (e.g., `RetryStrategyOptions`) holding configuration.
Predicates for which outcomes to handle are declared via `PredicateBuilder`.

### Testing patterns

- **`pytest`** for unit tests; **`hypothesis`** for property-based tests.
- **Deterministic time:** Always use `FakeTimeProvider` instead of real delays or `time.sleep` / `asyncio.sleep`.
- **Sync and async:** Cover both synchronous (`def`) and asynchronous (`async def`) execution paths.
- Shared helpers and fixtures live in `python/test/test_utils` and `python/test/conftest.py`.
- Coverage is collected in CI and uploaded to Codecov.

## General guidelines

- Always ensure code passes typing (`mypy`), linting (`ruff`), and tests (`pytest`) before committing changes.
- Do not change the public API without explicit request/discussion.
- Bug fixes should **always** include a test that would fail without the corresponding fix.
- Do not introduce new dependencies unless specifically requested.

## Path-specific instructions

Path-specific coding conventions are located in [`.github/instructions`](.github/instructions):

- [`tests.instructions.md`](.github/instructions/tests.instructions.md) — pytest conventions, determinism, mocking, and coverage.
- [`library.instructions.md`](.github/instructions/library.instructions.md) — outcome handling, sync/async parity, time providers, and thread/task safety.
- [`compatibility.instructions.md`](.github/instructions/compatibility.instructions.md) — Python version targets and type safety.
- [`performance.instructions.md`](.github/instructions/performance.instructions.md) — allocations, slots, and context reuse.
- [`benchmarks.instructions.md`](.github/instructions/benchmarks.instructions.md) — benchmark benchmarks with pytest-benchmark.
- [`public-api.instructions.md`](.github/instructions/public-api.instructions.md) — public contract stability and `__all__` definitions.
- [`docs.instructions.md`](.github/instructions/docs.instructions.md) — documentation standards and runnable samples.

