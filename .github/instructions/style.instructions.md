---
applyTo: "python/**,**/*.py"
---

# Code Style & Documentation Instructions (NumPy Style & Comprehensive Commenting)

All Python code written for SqawkPy must adhere to strict commenting and documentation standards. Code in this repository is expected to be self-explanatory, maintainable, and directly consumable by Sphinx documentation builders (using `sphinx.ext.napoleon`).

---

## 1. Mandatory Commenting Standard

Every single module, class, method, function, and key code block **must** be commented:

1. **Modules**: Every `.py` file must begin with a descriptive module docstring explaining its purpose, role within SqawkPy, and key exports.
2. **Classes**: Every class (public or internal) must have a NumPy-style docstring explaining its responsibility, constructor parameters, attributes, and memory/concurrency characteristics.
3. **Methods & Functions**: Every method, function, property, and classmethod must have a complete NumPy-style docstring detailing `Parameters`, `Returns`, and `Raises`.
4. **Key Code Blocks**: Every non-trivial block of logic (e.g., thread/async synchronization, pool recycling, state machine transitions, retry loops, error interception, cancellation checks) must include inline comments detailing *why* the logic is implemented that way.

---

## 2. NumPy Docstring Format

All docstrings must follow the **NumPy Docstring Standard** supported by Sphinx Napoleon.

### Function / Method Template

```python
def execute_core(
    self,
    callback: Callable[[ResilienceContext, TState], Outcome[TResult]],
    context: ResilienceContext,
    state: TState,
) -> Outcome[TResult]:
    """
    Execute the resilience strategy around the user-provided callback.

    Interceps executions, captures any unhandled exceptions into an Outcome,
    and applies strategy-specific resilience logic.

    Parameters
    ----------
    callback : Callable[[ResilienceContext, TState], Outcome[TResult]]
        The user-provided action or next pipeline component to execute.
    context : ResilienceContext
        The per-execution resilience context carrying metadata, properties,
        and cancellation signals.
    state : TState
        Custom state passed to the callback to avoid closure allocations.

    Returns
    -------
    Outcome[TResult]
        The result of the operation, containing either a successful value
        or an encapsulated exception.

    Raises
    ------
    ValueError
        If `context` or `callback` is None.

    Notes
    -----
    In accordance with the 'Return Outcomes, Don't Throw' rule, user-thrown
    exceptions must be captured into an Outcome rather than escaped.
    """
```

### Class Template

```python
class ResilienceContextPool:
    """
    Thread-safe object pool for leasing and recycling ResilienceContext instances.

    Minimizes object allocation and garbage collection overhead on high-throughput
    execution paths by reusing context objects.

    Parameters
    ----------
    max_size : int, optional
        The maximum number of idle context instances retained in the pool
        (default is 1024).

    Attributes
    ----------
    max_size : int
        The capacity limit for cached instances in the pool.

    Notes
    -----
    Contexts leased via `get()` must always be returned via `return_to_pool()`
    within a `try...finally` block to avoid pool starvation.
    """
```

### Property Template

```python
@property
def is_synchronous(self) -> bool:
    """
    Indicate whether the active execution pipeline is running synchronously.

    Returns
    -------
    bool
        True if the execution is synchronous; False if running within an
        asynchronous event loop.
    """
```

---

## 3. Inline Comments on Key Code Blocks

Do not leave complex blocks unannotated. Specifically, always comment:

- **Concurrency & Locks**: Explain what shared state is being protected and why the lock scope is bounded.
  ```python
  # Synchronize access to the internal idle list to prevent race conditions across worker threads
  with self._lock:
      context = self._pool.pop() if self._pool else ResilienceContext()
  ```
- **Error Interception**: Explain why exceptions are caught and wrapped.
  ```python
  # Intercept callback exceptions to honor the "Return Outcomes, Don't Throw" design principle
  try:
      outcome = callback(context, state)
  except Exception as ex:
      outcome = Outcome.from_exception(ex)
  ```
- **Resource & Memory Management**:
  ```python
  # Reset context fields before returning to pool to prevent state leakage across different execution call sites
  context.reset()
  ```
- **Mathematical / Algorithm Steps**:
  ```python
  # Apply decorrelated jitter formula: min(max_delay, random(base_delay, current_delay * 3))
  delay = min(self.max_delay, self._randomizer(self.base_delay, current_delay * 3.0))
  ```

---

## 4. Section Formatting Rules

1. Section headers (`Parameters`, `Returns`, `Raises`, `Attributes`, `Notes`, `Examples`) must be followed by an underline of dashes matching the exact length of the header name.
2. Parameter descriptions must specify types consistent with PEP 484 type annotations.
3. Keep descriptions grammatically complete and punctuated.

