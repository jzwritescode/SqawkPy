---
applyTo: "python/src/**/*.py,src/**/*.py"
---

# Library Code

Conventions for the library code of SqawkPy (Python port of Polly). Where an existing file's style differs from these rules, the file's style takes precedence.

## Strategy Implementation

- **Return outcomes, don't throw.** Strategies communicate failures and results by returning an `Outcome[TResult]` (e.g. `Outcome.from_exception(exc)`) from core execution, rather than throwing. Exceptions raised by user callbacks must be captured into an outcome, not allowed to escape the pipeline unexpectedly.
- **Support both synchronous and asynchronous execution.** The same strategy architecture must support both synchronous (`execute`) and asynchronous (`execute_async`) execution. Check `ResilienceContext.is_synchronous` and use non-blocking patterns rather than introducing blocking thread calls or sync-over-async workarounds.
- **Use `TimeProvider` for all time.** Never read the system clock or delay directly (`time.time()`, `time.monotonic()`, `time.sleep()`, or `asyncio.sleep()` without a `TimeProvider`). Always use the `TimeProvider` supplied through the strategy's builder context or `ResilienceContext` so that behavior is deterministic, controllable, and testable.
- **Cancellation.** Respect `ResilienceContext.cancellation_token` or cancellation signals. For asynchronous executions, respect and propagate `asyncio.CancelledError`.
- **Telemetry.** Strategies report events through `ResilienceStrategyTelemetry`. New events, or changes to existing events, are observable behavior changes for telemetry consumers and must be documented in `docs/advanced/telemetry.md`.
- **Options validation.** Strategy options are validated when the pipeline is built (e.g. valid duration ranges, required callbacks). New options should follow the same pattern, raising `ValueError` for invalid configurations, with their valid range and default values documented.
- **Thread-safety and task-safety.** A built pipeline is shared and executed concurrently across threads or async tasks. Strategies must not store per-execution state in `self` attributes; per-execution state belongs in local variables or on the `ResilienceContext`. Stateful components (such as circuit breaker state controllers) must be safe under concurrent execution using thread/async locks.
- **Sibling code.** A fix or pattern in one strategy often applies to others (retry, circuit breaker, fallback, hedging, timeout, rate limiter, and chaos strategies in Simmy), and to both generic and untyped variants.

