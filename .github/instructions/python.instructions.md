---
applyTo: "python/**,**/*.py"
---

# Python Idioms & Nuances (Favor Python over .NET Constructs)

When porting or extending SqawkPy from .NET Polly, **always favor idiomatic Python patterns over literal C# translations**. The goal is a first-class Python library that matches Polly's algorithms and resilience guarantees, not "C# written in Python syntax".

---

## 1. Naming Conventions (PEP 8)

- **Methods, functions, attributes, and variables:** Use `snake_case` (e.g., `execute_async`, `is_synchronous`, `from_result`, `try_get_result`).
  - *Anti-pattern:* `ExecuteAsync`, `FromResult`, `IsSynchronous`.
- **Classes, type aliases, and exceptions:** Use `PascalCase` (e.g., `ResiliencePipeline`, `TimeoutRejectedException`, `Outcome`).
- **Constants:** Use `UPPER_SNAKE_CASE` (e.g., `DEFAULT_TIMEOUT`, `MAX_ATTEMPTS`).
- **Internal / Private symbols:** Prefix with a single underscore (e.g., `_component`, `_execute_core`).

---

## 2. Asynchronous & Synchronous Execution

- **No sync-over-async:** In Python, calling `asyncio.run()` or `loop.run_until_complete()` inside an already running event loop raises a `RuntimeError` or causes deadlocks. Never bridge async code into synchronous execution with nested event loop hacks.
- **Dual execution paths:** Maintain clean, explicit execution entry points:
  - `execute(callback, *args, **kwargs)` for synchronous functions.
  - `execute_async(coro_callback, *args, **kwargs)` for asynchronous coroutines (`async def`).
- **Event loop cooperation:** Use `await asyncio.sleep(...)` via `TimeProvider.delay_async(...)` for async delays. Never use blocking `time.sleep()` on async execution paths.

---

## 3. Object Model & Memory Management

- **No value-type structs:** Python has no stack-allocated value types or structs. Do not create artificial wrapper classes simulating C# structs.
- **Use `__slots__` for hot paths:** Core per-execution data structures (`Outcome`, `ResilienceContext`, argument types) must declare `__slots__` to eliminate per-instance `__dict__` overhead, reduce memory consumption by ~60%, and accelerate attribute lookups.
- **Context reuse with pooling:** Use `ResilienceContextPool` for hot-path executions. Contexts retrieved with `get()` must always be returned with `return_to_pool()` in a `try...finally` block.

---

## 4. Static Typing & Generics

- **Type erasure at runtime:** Python generics (`Generic[TResult]`, `TypeVar`) are purely static and erased at runtime.
  - Do not rely on runtime reflection of generic arguments (e.g., `typeof(T)`).
  - Use `isinstance()` for concrete type checks and `PredicateBuilder` for runtime outcome matching.
- **Protocols over nominal interfaces:** Prefer `typing.Protocol` (structural subtyping / static duck typing) over heavy abstract base class hierarchies unless code sharing is required.
- **Modern type annotations:** Use PEP 585/604 syntax: `list[str]`, `dict[str, Any]`, `T | None` (instead of `Union[T, None]`), with `from __future__ import annotations`.

---

## 5. Properties vs Getters/Setters

- **Pythonic attributes and `@property`:** Use public attributes for simple data, or `@property` decorators when computed or read-only access is needed.
- **Avoid verbose JavaBean / C# accessors:** Do not write methods like `get_timeout()` and `set_timeout(val)` when `strategy.timeout` or `@property` is standard.

---

## 6. Exceptions & Error Handling

- **Python exception hierarchy:** Use standard Python exceptions (`ValueError`, `TypeError`, `TimeoutError`, `RuntimeError`) or domain-specific subclasses. Do not port .NET exceptions literally (e.g., avoid `ArgumentNullException`; use `ValueError` with `"Parameter cannot be None"`).
- **Exception chaining:** Always preserve the root cause when raising new exceptions using explicit chaining:
  ```python
  raise TimeoutRejectedException("Operation timed out", timeout) from original_error
  ```
- **"Return Outcomes, Don't Throw":** Inside strategy execution middleware, intercept user callback exceptions and wrap them in `Outcome.from_exception(exc)` instead of allowing unhandled exceptions to escape across strategies.

---

## 7. Cancellation Semantics

- **Async cancellation:** Respect Python's native cancellation model (`asyncio.CancelledError`). When an async task is cancelled, clean up resources in `finally` blocks and re-raise or wrap `asyncio.CancelledError` as appropriate.
- **Synchronous cancellation:** Use `threading.Event` or cooperative tokens (`cancellation_token.is_cancellation_requested`) rather than attempting thread abortion.

---

## 8. Resource Management & Context Managers

- **Context managers over `IDisposable`:** Use `__enter__` / `__exit__` and `__aenter__` / `__aexit__` with Python's `with` / `async with` statements.
- Never require callers to manually call `.dispose()`; provide a context manager or hook into pool recycling.

---

## 9. Collections & Functional Idioms

- **Comprehensions over LINQ:** Use Python list, dict, and set comprehensions, generator expressions, or `any()` / `all()` instead of attempting to mimic C# LINQ methods (`.Select()`, `.Where()`, `.FirstOrDefault()`).
- Use standard mapping protocols (`dict`, `collections.abc.Mapping`).

---

## 10. Dependency Hygiene

- **Zero unnecessary dependencies:** Maintain zero external runtime dependencies for core resilience features. Use the Python standard library (`asyncio`, `time`, `dataclasses`, `threading`, `datetime`) rather than pulling in external packages.

