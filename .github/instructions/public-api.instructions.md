---
applyTo: "python/src/**,src/**"
---

# Public API

Public API changes are a **blocking** review gate. The public API contract must remain stable and backward-compatible.

- Every public module must explicitly declare its public members via `__all__`. Any symbol not listed in `__all__` or prefixed with `_` is considered internal.
- For any public API change, ensure that:
  1. The change is discussed or linked to an agreed-upon issue.
  2. The change is additive. Renaming functions, removing classes/methods, altering parameter order or types, or breaking return types are breaking changes.
  3. The API follows idiomatic Python conventions (`snake_case` functions/methods, `PascalCase` classes, descriptive parameter names).
  4. Both synchronous and asynchronous counterparts are supported and consistent.
  5. The new API has complete docstrings, type annotations, tests, and updated documentation in `docs/`.
- Behavioral changes to existing public APIs (such as default option values, handled exceptions, or event emissions) are breaking changes even if signatures remain unchanged.
- Internal types and helper functions should be prefixed with `_`. Do not expose internal members in `__all__` or remove underscores solely to facilitate testing.

