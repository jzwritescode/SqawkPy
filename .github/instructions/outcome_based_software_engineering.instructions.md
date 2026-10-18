---
applyTo: "**"
---

# Outcome-Based Software Engineering (OBSE) Instructions

## Philosophy

Outcome-Based Software Engineering reframes how progress is measured. Instead of
tracking tasks completed, files written, or lines of code committed, progress is
measured exclusively through **verified, observable outcomes**: working software
that satisfies a quality gate.

In SqawkPy, the outcome is always the same unit:

> *A resilience strategy or pipeline component that behaves identically to its
> .NET Polly counterpart, is fully typed, is fully documented with NumPy
> docstrings, and whose test suite passes all quality gates.*

No increment is considered "done" until that entire unit is green.

---

## Core Principles

### 1. Outcomes Over Output

**Reject** these as measures of progress:
- "I wrote the `RetryResilienceStrategy` class" (output, not outcome).
- "50% of the methods are implemented" (partial state, not verified).
- "The file exists" (presence, not correctness).

**Accept** only these as measures of progress:
- `pytest python/test/test_retry.py` exits 0 with zero failures.
- `mypy --strict python/src` exits 0 with no errors.
- `ruff check python` exits 0 with no violations.
- `pytest --cov=sqawk --cov-report=term-missing` reports ≥ 95% coverage.
- Every public symbol has a NumPy-style docstring.

### 2. Increment-by-Increment Delivery

Break work into the smallest increment that can independently pass the Definition
of Done gate. An increment is one **strategy, one module, or one pipeline
feature** — not a phase or a milestone.

Each increment follows a fixed delivery sequence:

```
Analysis → Design → Implementation → Tests → Type Check → Coverage → Docs → Gate
```

Do **not** skip steps. Do not merge steps. Do not declare done before the gate.

### 3. Behavioral Fidelity, Not Syntax Parity

The .NET source in `dotnet/` is the **behavioral specification**, not a template
to transliterate. Every algorithm, backoff formula, jitter calculation, and
circuit-breaker state transition must produce identical outputs for identical
inputs. The Python surface, however, must be idiomatic:

- `snake_case` identifiers, not `PascalCase`.
- `async def` / `await`, not `Task<T>` / `ContinueWith`.
- Context managers (`with`), not `IDisposable`.
- Dataclasses or `__slots__` classes, not struct-like value types.
- `threading.Lock` / `asyncio.Lock`, not `Monitor` / `SemaphoreSlim`.

### 4. Traceability

Every public component in `python/src/sqawk/` must trace back to one or more
.NET source or test files in `dotnet/`. Record the trace in the docstring or in
an inline comment at the top of the module:

```python
# Behavioral specification: dotnet/src/Polly/Retry/RetryResilienceStrategy.cs
# Reference tests:         dotnet/test/Polly.Core.Tests/Retry/RetryResilienceStrategyTests.cs
```

This traceability requirement ensures behavioral parity is always verifiable by
reading the .NET source and its tests side-by-side with the Python counterpart.

### 5. Test-First Verification

Write the **test skeleton before or alongside the implementation**, not after.
Tests are the executable specification of the expected outcome. A test that
cannot yet pass because the implementation is incomplete is progress — it
documents the gap between current state and the desired outcome.

Prefer a failing test that describes correct behavior to working code with no
test coverage.

---

## Definition of Done (DoD) Gate

Every increment must clear **all** of the following gates before it is closed.
No exceptions. No partial credit.

### Gate 1 — Behavioral Correctness

```bash
pytest python/test
```

- All tests pass (exit 0, zero failures, zero errors).
- Both synchronous (`def`) and asynchronous (`async def`) execution paths are
  covered by dedicated test cases.
- No test uses real wall-clock time: `FakeTimeProvider` is mandatory for all
  time-dependent logic. See `tests.instructions.md`.

### Gate 2 — Type Safety

```bash
mypy python/src python/test
```

- Exits 0 with zero errors.
- `--strict` mode enforced (configured in `python/pyproject.toml`).
- No `type: ignore` suppression without an explanatory inline comment that
  references the specific mypy limitation being worked around.

### Gate 3 — Linting and Formatting

```bash
ruff check python
ruff format --check python
```

- Both exit 0.
- No `# noqa` suppression without an explanatory inline comment.

### Gate 4 — Coverage

```bash
pytest python/test --cov=sqawk --cov-report=term-missing
```

- Line coverage for the new increment ≥ 95%.
- Branch coverage must also be checked (`--cov-branch`) for strategy state
  machines and predicate dispatch paths.
- No coverage exclusion (`# pragma: no cover`) without explicit justification
  in a code comment.

### Gate 5 — Documentation Completeness

Every public symbol added in the increment must have:

- A **module-level docstring** describing purpose, behavioral specification
  trace, and any important constraints.
- A **class docstring** with `Parameters`, `Attributes`, `Notes`, and
  `Examples` sections (NumPy format). See `style.instructions.md`.
- A **method docstring** with `Parameters`, `Returns`, `Raises`, and
  `Notes` sections for every non-trivial method.
- **Block comments** on every non-obvious code block: lock acquisition, pool
  operations, backoff calculations, state transitions, predicate evaluations.

### Gate 6 — No Regression

```bash
pytest python/test
```

- All tests that passed before the increment still pass.
- Zero previously-passing tests may be marked `xfail` or skipped without
  prior discussion.

---

## Delivery Workflow

### Step 1: Analysis

Inspect the corresponding .NET source in `dotnet/src/Polly*` and
`dotnet/test/Polly*`. Extract:

1. The algorithm or behavior being implemented.
2. All configuration options and their defaults.
3. All edge cases exercised in the .NET test suite.
4. All numeric formulas (backoff, jitter, sampling windows, thresholds).
5. All state transitions and their guards.

Output: an analysis brief (inline comment block at top of the design document
or implementation file) that a reviewer can use to verify correctness without
reading the .NET source.

### Step 2: Design

Translate the analysis into an idiomatic Python interface specification:

1. Define the public class and method signatures with type annotations.
2. Choose the `__slots__` layout for hot-path classes.
3. Specify the sync entry point (`execute`) and async entry point
   (`execute_async`) separately — never one calling the other.
4. Specify thread-safety requirements and which locks are needed.
5. Specify which `Options` dataclass holds configuration and what validations
   it enforces.

### Step 3: Implementation

Write the production code in `python/src/sqawk/`. Follow all rules in:

- `python.instructions.md` — idioms, anti-patterns, async/sync rules.
- `style.instructions.md` — NumPy docstrings, block comments.
- `library.instructions.md` — Outcome handling, TimeProvider injection.
- `performance.instructions.md` — `__slots__`, allocation discipline.
- `public-api.instructions.md` — `__all__`, snake_case, no leaking internals.
- `design_patterns.instructions.md` — Pipeline, Strategy, Builder, State
  Machine, Sentinel patterns.

### Step 4: Tests

Write the pytest suite in `python/test/`. Follow all rules in:

- `tests.instructions.md` — determinism, FakeTimeProvider, sync+async parity.
- Cover every edge case identified in Step 1.
- Add `hypothesis` property-based tests for numeric invariants (jitter bounds,
  sampling windows, threshold computations).

### Step 5: Gate Verification

Run all four commands. Fix any failures before declaring the increment done:

```bash
mypy python/src python/test
ruff check python && ruff format --check python
pytest python/test
pytest python/test --cov=sqawk --cov-report=term-missing --cov-branch
```

### Step 6: Documentation

- Update `python/eng/IMPLEMENTATION_PLAN.md` to reflect the component's status.
- Verify that Sphinx can parse every docstring (run `python -m doctest` on
  examples if present).
- Add a runnable example to `python/eng/` or a `docs/` subfolder if the
  component represents a major user-facing feature.

---

## Sprint Gates

Each sprint concludes only when **every component assigned to that sprint** has
cleared the full DoD gate. A sprint is not complete if even one component is
missing a test, has a mypy error, or lacks a docstring.

Sprint definitions and component assignments are maintained in
`python/eng/IMPLEMENTATION_PLAN.md`. Refer to that document for the authoritative
list of components per sprint.

---

## What "Working Software" Means Here

In SqawkPy, "working software" has a precise definition:

| Criterion | Verification |
|-----------|-------------|
| Correct resilience behavior | Pytest test suite mirrors .NET test coverage |
| Identical numeric outputs | Hypothesis property tests on formulas |
| Strict type safety | `mypy --strict` exits 0 |
| No style drift | `ruff check` + `ruff format --check` exit 0 |
| High coverage | `pytest --cov` ≥ 95% line + branch |
| Sphinx-ready docs | Every public symbol has a NumPy docstring |
| Deterministic tests | All time-dependent tests use `FakeTimeProvider` |
| Dual-mode execution | Both sync and async paths exercised in tests |

Software that does not satisfy **all** rows of this table is not working
software for the purposes of SqawkPy's OBSE process.

---

## Anti-Patterns to Avoid

The following behaviors violate OBSE principles and are prohibited:

| Anti-Pattern | Why It Violates OBSE |
|---|---|
| Merging code without passing tests | Progress cannot be verified |
| Skipping docstrings to "come back later" | Documentation debt is outcome debt |
| Writing sync only, deferring async | Async path is half the outcome |
| Using `time.sleep` in tests | Non-determinism poisons outcome verification |
| Suppressing mypy with `type: ignore` silently | Type safety is a gate, not a suggestion |
| Marking tests `xfail` without a tracking issue | Hides regressions |
| Declaring a sprint done with any open gate | Partial done is not done |
| Copying .NET C# structure without Python idioms | Behavioral parity ≠ structural parity |

---

## References

- Implementation plan and sprint assignments: [`python/eng/IMPLEMENTATION_PLAN.md`](../../python/eng/IMPLEMENTATION_PLAN.md)
- Coding idioms and anti-patterns: [`.github/instructions/python.instructions.md`](python.instructions.md)
- Documentation standards: [`.github/instructions/style.instructions.md`](style.instructions.md)
- Test conventions: [`.github/instructions/tests.instructions.md`](tests.instructions.md)
- Library design contracts: [`.github/instructions/library.instructions.md`](library.instructions.md)
- Design patterns: [`.github/instructions/design_patterns.instructions.md`](design_patterns.instructions.md)
- Agent orchestration: [`.github/agents/agile_project_manager.md`](../agents/agile_project_manager.md)

