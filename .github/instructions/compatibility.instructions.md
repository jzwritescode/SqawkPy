---
applyTo: "python/src/**/*.py,src/**/*.py"
---

# Compatibility

- **Python versions.** Library code must support Python 3.10 and later (3.10, 3.11, 3.12, 3.13). Watch for syntax and stdlib features introduced in newer versions without polyfills or guards (use `typing_extensions` where necessary for backported typing features).
- **Type safety.** All code must be strictly type-annotated according to PEP 484, PEP 585, and PEP 604. Packages must include the `py.typed` marker (PEP 561) to support downstream type checkers (mypy, pyright).
- **Cross-platform.** Library code and tests must execute and pass on Linux, macOS, and Windows. Avoid OS-dependent path handling, signal dependencies, or OS-specific asyncio event loop quirks.

