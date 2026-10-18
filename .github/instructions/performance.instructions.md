---
applyTo: "python/src/**/*.py,src/**/*.py"
---

# Performance and Allocations

SqawkPy's execution paths should minimize overhead and memory allocations on the hot path.

- Flag avoidable allocations on the execution path: unnecessary dictionary instantiations, closures capturing broad scope when static functions or explicit state arguments suffice, and unneeded object creations during steady-state execution.
- Prefer efficient structures: use `__slots__` on performance-critical core classes (`Outcome`, `ResilienceContext`, arguments dataclasses).
- Prefer object pooling and reuse patterns where applicable, such as `ResilienceContextPool` for contexts (every `get()` needs a matching `return_to_pool()`, including within `try...finally` blocks).
- Changes to hot paths and PRs claiming performance improvements should include `pytest-benchmark` results comparing baseline against the proposed change.

