---
applyTo: "python/src/**/*.py,src/**/*.py"
---

# Design Patterns Instructions for SqawkPy

SqawkPy ports and refines the core design patterns of .NET Polly v8 into an idiomatic Python architecture. When authoring or reviewing strategies, components, and builders, adhere to these architectural patterns:

---

## 1. Pipeline Pattern (Chain of Responsibility / Middleware)

- **Execution Flow:** `ResiliencePipeline` coordinates an ordered sequence of `ResilienceStrategy` components.
- **Middleware Delegation:** Each strategy intercepts the call, executes its resilience logic (before/after), and delegates to the next component in the chain.
- **Uniform Invocation:** The pipeline handles execution wrapping so that client code sees a uniform `execute(...)` / `execute_async(...)` interface regardless of how many strategies are composed.

---

## 2. Strategy Pattern

- **Interchangeable Behaviors:** Each resilience policy (`Retry`, `CircuitBreaker`, `Timeout`, `RateLimiter`, `Fallback`, `Hedging`) is an encapsulated strategy subclassing `ResilienceStrategy`.
- **Stateless Execution:** Strategies must be stateless across individual executions. Per-call variables must live on the call stack or on `ResilienceContext`.
- **Sibling Consistency:** Common configuration patterns (such as `ShouldHandle` predicates, delay generators, and event callbacks) must follow identical naming and signature conventions across all strategies.

---

## 3. Fluent Builder Pattern

- **Composition via Builder:** Pipelines are constructed using `ResiliencePipelineBuilder`.
- **Chainable Methods:** Configuration methods (e.g., `add_retry(...)`, `add_timeout(...)`, `add_circuit_breaker(...)`) return `self` to support fluent chaining.
- **Validation at Build Time:** Builder methods and options objects validate configuration parameters (e.g., non-negative timeouts, positive retry attempts, valid rate limits) when `build()` is invoked, raising `ValueError` early rather than failing at runtime.

---

## 4. Outcome / Result Pattern ("Return Outcomes, Don't Throw")

- **Encapsulated Return:** Core strategy execution returns `Outcome[TResult]` encapsulating either a successful value or a captured exception.
- **No Unhandled Escalation:** Exceptions raised by user callbacks or target functions are captured into `Outcome.from_exception(exc)` inside strategy middleware.
- **Rethrow Boundary:** Only at the outermost boundary of `pipeline.execute(...)` is `outcome.throw_if_exception()` called to unpack the result or raise the error to the caller.

---

## 5. Object Pool Pattern

- **Context Recycling:** `ResilienceContextPool` provides a thread-safe pool for leasing (`get()`) and reclaiming (`return_to_pool()`) `ResilienceContext` instances.
- **Zero/Low Allocation:** Avoids allocating a new context dictionary or object on every request on hot execution paths.
- **Guaranteed Cleanup:** The pipeline always executes context return within a `finally` block, ensuring no pool starvation occurs even when exceptions are raised.

---

## 6. State Machine Pattern

- **Circuit Breaker States:** The circuit breaker strategy operates a strict finite state machine:
  - `Closed`: Normal operation, tracking failure metrics.
  - `Open`: Tripped state, rejecting executions immediately with `BrokenCircuitException`.
  - `HalfOpen`: Trial period allowing a limited probe attempt to test upstream recovery.
- **Thread/Task Synchronization:** State transitions must be thread-safe and task-safe using synchronization primitives.

---

## 7. Clock & Dependency Injection Pattern

- **Abstract Time:** Strategies depend on the `TimeProvider` abstraction rather than system sleep or clock APIs.
- **Testability via Injection:** Production code receives `SystemTimeProvider` by default; unit and integration tests inject `FakeTimeProvider` to control time deterministically.

---

## 8. Sentinel / Singleton Pattern

- **Void Operations:** `VoidResult` represents operations that do not return a value. It is implemented as a singleton to allow fast identity checks (`is VoidResult`).
- **Uninitialized State:** `UnknownResult` is used as an uninitialized sentinel for recycled contexts.

