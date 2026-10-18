---
applyTo: "python/bench/**,bench/**"
---

# Benchmarks

- Benchmarks live in `python/bench/` and use `pytest-benchmark`.
- Pipeline construction belongs in helper fixtures or setup routines, isolated from the benchmarked execution loop.
- Benchmarks should measure both synchronous (`execute`) and asynchronous (`execute_async`) execution paths.
- Avoid real delays or wall-clock waits in benchmarks; use `FakeTimeProvider` or zero-delay mocks where time-dependent strategies (like retry or timeout) are measured.
- Benchmark result artifacts should only be committed when that is the explicit purpose of the PR.

