"""
Resilience context and pooling module.

This module provides the execution context infrastructure for SqawkPy pipelines,
including strongly-typed property storage (`ResiliencePropertyKey`,
`ResilienceProperties`), per-execution state tracking (`ResilienceContext`),
and thread-safe context leasing and recycling (`ResilienceContextPool`).

Exports
-------
ResiliencePropertyKey
    Strongly-typed key for attaching metadata to a ResilienceProperties bag.
ResilienceProperties
    Custom property container attached to ResilienceContext.
ResilienceContext
    Per-execution context carrying operation keys, cancellation, and metadata.
ResilienceContextPool
    Thread-safe pool for leasing and returning ResilienceContext instances.
SharedResilienceContextPool
    Global default instance of ResilienceContextPool.
"""

from __future__ import annotations

import threading
from typing import Any, Generic, TypeVar

from sqawk.outcome import VoidResult, _VoidResultType

TValue = TypeVar("TValue")
TResult = TypeVar("TResult")


class _UnknownResultType:
    """Marker type for uninitialized resilience context."""

    pass


# Sentinel indicating that the context result type has not been initialized
UnknownResult = _UnknownResultType()


class ResiliencePropertyKey(Generic[TValue]):
    """
    Strongly-typed key used by `ResilienceProperties` to store and retrieve metadata.

    Parameters
    ----------
    key : str
        The string identifier for this property key.

    Attributes
    ----------
    key : str
        The string name of the key.

    Raises
    ------
    ValueError
        If `key` is empty or None.

    Notes
    -----
    Uses `__slots__` to minimize memory allocation.
    """

    __slots__ = ("_key",)

    def __init__(self, key: str) -> None:
        if not key:
            raise ValueError("Key cannot be empty or None.")
        self._key = key

    @property
    def key(self) -> str:
        """
        Get the string name of the property key.

        Returns
        -------
        str
            The key name identifier.
        """
        return self._key

    def __str__(self) -> str:
        """
        Return the string representation of the key.

        Returns
        -------
        str
            The underlying key name.
        """
        return self._key

    def __repr__(self) -> str:
        """
        Return the debug representation of the property key.

        Returns
        -------
        str
            Formatted representation including the key name.
        """
        return f"ResiliencePropertyKey({self._key!r})"

    def __eq__(self, other: object) -> bool:
        """
        Compare two property keys for equality based on their key string.

        Parameters
        ----------
        other : object
            The other object to compare.

        Returns
        -------
        bool
            True if both objects are ResiliencePropertyKey instances with matching keys.
        """
        if isinstance(other, ResiliencePropertyKey):
            return self._key == other._key
        return False

    def __hash__(self) -> int:
        """
        Calculate hash based on the key string for dictionary lookups.

        Returns
        -------
        int
            Hash value of the key string.
        """
        return hash(self._key)


class ResilienceProperties:
    """
    Collection of custom resilience properties attached to a ResilienceContext.

    Provides a typed key-value property bag for passing custom options, telemetry tags,
    or execution metadata across pipeline strategies.

    Attributes
    ----------
    options : dict of str to Any
        The raw underlying options dictionary.
    """

    __slots__ = ("_options",)

    def __init__(self) -> None:
        # Pre-allocate dictionary for options storage
        self._options: dict[str, Any] = {}

    @property
    def options(self) -> dict[str, Any]:
        """
        Get the raw underlying dictionary storing properties.

        Returns
        -------
        dict of str to Any
            Dictionary mapping string keys to property values.
        """
        return self._options

    def set(self, key: ResiliencePropertyKey[TValue], value: TValue) -> None:
        """
        Set the property value for the specified strongly-typed key.

        Parameters
        ----------
        key : ResiliencePropertyKey[TValue]
            The strongly-typed property key.
        value : TValue
            The value to store for the key.
        """
        self._options[key.key] = value

    def try_get_value(self, key: ResiliencePropertyKey[TValue]) -> tuple[bool, TValue | None]:
        """
        Attempt to retrieve the property value associated with the specified key.

        Parameters
        ----------
        key : ResiliencePropertyKey[TValue]
            The strongly-typed property key to look up.

        Returns
        -------
        tuple of (bool, TValue or None)
            A tuple where the first element is True if the key was found,
            and the second element is the associated value.
        """
        # Check dictionary existence
        if key.key in self._options:
            val = self._options[key.key]
            return True, val
        return False, None

    def get_value(self, key: ResiliencePropertyKey[TValue], default_value: TValue) -> TValue:
        """
        Retrieve the property value for the specified key or return a fallback default.

        Parameters
        ----------
        key : ResiliencePropertyKey[TValue]
            The strongly-typed property key.
        default_value : TValue
            The fallback value to return if the key is not present.

        Returns
        -------
        TValue
            The stored value if found; otherwise `default_value`.
        """
        found, val = self.try_get_value(key)
        if found:
            return val  # type: ignore[return-value]
        return default_value

    def add_or_replace_properties(self, other: ResilienceProperties) -> None:
        """
        Copy all property entries from another ResilienceProperties instance.

        Parameters
        ----------
        other : ResilienceProperties
            The source properties instance to copy from.
        """
        # Batch update dictionary entries
        self._options.update(other._options)

    def clear(self) -> None:
        """Clear all stored properties."""
        self._options.clear()


class ResilienceContext:
    """
    Execution context assigned to a single invocation of a ResiliencePipeline.

    Carries per-execution state through strategies, including operation keys,
    cancellation tokens, sync/async execution flags, and custom properties.

    Attributes
    ----------
    operation_key : str or None
        A low-cardinality string identifying the call site for metrics and logs.
    cancellation_token : Any
        Cancellation signal (e.g., threading.Event, token, or sentinel).
    continue_on_captured_context : bool
        Flag indicating context capture preference.
    properties : ResilienceProperties
        Custom property bag associated with this execution.
    is_synchronous : bool
        True if the execution is synchronous; False if asynchronous.
    result_type : Any
        The expected result type of the execution.
    is_void : bool
        True if the execution represents an operation returning void / None.
    is_initialized : bool
        True if the context has been initialized for an execution.

    Notes
    -----
    Do not reuse an active ResilienceContext instance across multiple executions.
    Always obtain a context from `ResilienceContextPool.get()` and return it via
    `ResilienceContextPool.return_to_pool()`.
    """

    __slots__ = (
        "operation_key",
        "cancellation_token",
        "continue_on_captured_context",
        "properties",
        "_is_synchronous",
        "_result_type",
    )

    def __init__(self) -> None:
        self.operation_key: str | None = None
        self.cancellation_token: Any = None
        self.continue_on_captured_context: bool = False
        self.properties: ResilienceProperties = ResilienceProperties()
        self._is_synchronous: bool = False
        self._result_type: Any = UnknownResult

    @property
    def is_synchronous(self) -> bool:
        """
        Indicate whether the execution is running synchronously.

        Returns
        -------
        bool
            True for synchronous execution; False for asynchronous execution.
        """
        return self._is_synchronous

    @property
    def result_type(self) -> Any:
        """
        Get the type of the result associated with this execution.

        Returns
        -------
        Any
            The expected return type, or UnknownResult if uninitialized.
        """
        return self._result_type

    @property
    def is_void(self) -> bool:
        """
        Indicate whether the execution produces a void result.

        Returns
        -------
        bool
            True if result_type is VoidResult, _VoidResultType, or None.
        """
        return self._result_type is VoidResult or self._result_type is _VoidResultType or self._result_type is None

    @property
    def is_initialized(self) -> bool:
        """
        Indicate whether the context has been initialized.

        Returns
        -------
        bool
            True if initialized with a concrete result type; False otherwise.
        """
        return self._result_type is not UnknownResult

    def initialize(self, result_type: Any, is_synchronous: bool) -> ResilienceContext:
        """
        Initialize the context for a new pipeline execution.

        Parameters
        ----------
        result_type : Any
            The expected return type of the pipeline callback.
        is_synchronous : bool
            Flag indicating whether execution is synchronous.

        Returns
        -------
        ResilienceContext
            The initialized context instance (self).
        """
        self._result_type = result_type
        self._is_synchronous = is_synchronous
        return self

    def initialize_from(self, source: ResilienceContext, cancellation_token: Any = None) -> None:
        """
        Initialize this context by copying properties from another context.

        Parameters
        ----------
        source : ResilienceContext
            The source context to copy metadata and properties from.
        cancellation_token : Any, optional
            A new cancellation token to override on this context (default is None).
        """
        self.operation_key = source.operation_key
        self._result_type = source.result_type
        self._is_synchronous = source.is_synchronous
        self.continue_on_captured_context = source.continue_on_captured_context
        # Use provided cancellation token if given, otherwise inherit from source
        self.cancellation_token = cancellation_token if cancellation_token is not None else source.cancellation_token
        self.properties.add_or_replace_properties(source.properties)

    def reset(self) -> bool:
        """
        Reset context state so it can safely be returned to the pool.

        Returns
        -------
        bool
            True indicating successful reset.
        """
        # Clear all execution-specific fields to avoid state leaks between calls
        self.operation_key = None
        self.cancellation_token = None
        self.continue_on_captured_context = False
        self._is_synchronous = False
        self._result_type = UnknownResult
        self.properties.clear()
        return True


class ResilienceContextPool:
    """
    Thread-safe object pool for leasing and recycling ResilienceContext instances.

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

    def __init__(self, max_size: int = 1024) -> None:
        self._pool: list[ResilienceContext] = []
        self._lock = threading.Lock()
        self._max_size = max_size

    def get(
        self,
        operation_key: str | None = None,
        cancellation_token: Any = None,
        continue_on_captured_context: bool = False,
    ) -> ResilienceContext:
        """
        Lease a ResilienceContext from the pool or create a new one if empty.

        Parameters
        ----------
        operation_key : str or None, optional
            An operation key identifying the call site (default is None).
        cancellation_token : Any, optional
            Cancellation signal associated with this execution (default is None).
        continue_on_captured_context : bool, optional
            Whether execution continues on captured context (default is False).

        Returns
        -------
        ResilienceContext
            A leased context ready for initialization.
        """
        # Synchronize access to internal pool list across worker threads
        with self._lock:
            context = self._pool.pop() if self._pool else ResilienceContext()

        # Configure requested execution parameters on the leased context
        context.operation_key = operation_key
        context.cancellation_token = cancellation_token
        context.continue_on_captured_context = continue_on_captured_context
        return context

    def return_to_pool(self, context: ResilienceContext) -> None:
        """
        Return a leased ResilienceContext back to the pool after execution finishes.

        Parameters
        ----------
        context : ResilienceContext
            The context instance to recycle.

        Raises
        ------
        ValueError
            If `context` is None.
        """
        if context is None:
            raise ValueError("Context cannot be None.")

        # Reset all state before returning to pool to prevent cross-call contamination
        context.reset()

        # Reclaim the instance if below pool maximum capacity
        with self._lock:
            if len(self._pool) < self._max_size:
                self._pool.append(context)


# Global shared singleton context pool
SharedResilienceContextPool = ResilienceContextPool()
