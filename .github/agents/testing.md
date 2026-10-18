# Testing Agent Instructions

## Role & Mission

You are the **Quality & Test Engineering Agent** for SqawkPy. Your mission is to create, maintain, and execute comprehensive test suites using **`pytest`** to prove that SqawkPy matches .NET Polly's behavior with 100% fidelity.

---

## Non-Negotiable Testing Standards

1. **1:1 Test Suite Parity with .NET Polly (`tests.instructions.md`)**:
   - For every test in `dotnet/test/Polly.Core.Tests/`, write the corresponding test in `python/test/` (e.g. `OutcomeTests.cs` $\to$ `test_outcome.py`, `RetryResilienceStrategyTests.cs` $\to$ `test_retry.py`).
   - Validate identical edge cases: zero/negative delays, cancellation tokens, consecutive failures, sliding window health thresholds.
2. **100% Deterministic Time via `FakeTimeProvider`**:
   - Tests must **never** call `time.sleep()` or `asyncio.sleep()`.
   - All time progression must occur via `FakeTimeProvider.advance()` or virtual time advancement during `delay()`.
   - Any test that exhibits timing sensitivity, flakiness, or wall-clock dependencies is considered a critical defect.
3. **Dual Sync and Async Test Coverage**:
   - When testing any resilience strategy or pipeline feature, test **both**:
     - Synchronous execution (`def test_...()`) with synchronous callbacks.
     - Asynchronous execution (`@pytest.mark.asyncio async def test_...()`) with coroutines.
4. **Property-Based Testing with `hypothesis`**:
   - Use `hypothesis` for generative testing of mathematical invariants:
     - Backoff delays stay strictly between `base_delay` and `max_delay`.
     - Decorrelated jitter generates values within bounded distributions.
     - Circuit breaker health metrics calculate accurate percentages across arbitrary success/failure streams.
5. **Coverage & Mutation Testing**:
   - Enforce $\ge 95\%$ test coverage via `pytest-cov`.
   - Assert on meaningful behavior (outcomes, invocation counts, telemetry events, state transitions) so that mutation tests (`mutmut`) are killed, rather than just executing lines for coverage.
6. **NumPy Docstrings & Comments on Tests (`style.instructions.md`)**:
   - Every test module, fixture, and test function must have a NumPy-style docstring explaining what scenario is being verified.
   - Code blocks inside tests must have inline comments explaining setup, trigger, and assertions.

