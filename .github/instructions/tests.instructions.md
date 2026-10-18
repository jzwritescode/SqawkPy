---
applyTo: "python/test/**,test/**"
---

# Tests

- Test projects use `pytest`, standard Python `assert` statements (and `pytest.raises` for expected exceptions), `unittest.mock` / `pytest-mock` (`mocker`) for mocking, `FakeTimeProvider` for time, and `hypothesis` for property-based tests. Shared helpers and fixtures live in `python/test/test_utils` and `conftest.py`. Use these rather than introducing new libraries.
- **Bug fixes must include a regression test** that would fail without the fix. Tests for specific GitHub issues typically live in `python/test/issues/`, named after the issue number (e.g. `test_issue_2163.py`). Check that the test actually exercises the reported scenario.
- Tests must be deterministic. Flag tests that depend on real delays, wall-clock time, `time.sleep`, `asyncio.sleep`, or timing-sensitive races. Advance a `FakeTimeProvider` instead.
- When a change affects them, cover both synchronous (`def`) and asynchronous (`async def` with `pytest.mark.asyncio`), as well as generic/typed and non-generic execution paths.
- CI enforces code coverage (`pytest-cov`) and runs mutation tests (`mutmut`). Tests should assert on meaningful behavior (outcomes, event arguments, invocation counts) so that mutants are killed, rather than just executing code for coverage.
- Test code may use internal types and functions (conventionally prefixed with `_`). Do not make functions or classes public in `src/` (or add them to `__all__`) just for testing.

