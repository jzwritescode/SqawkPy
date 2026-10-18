"""ResilienceContext and associated properties and pooling."""

from __future__ import annotations

import threading
from typing import Any, Generic, TypeVar

from sqawk.outcome import VoidResult, _VoidResultType

TValue = TypeVar("TValue")
TResult = TypeVar("TResult")


class _UnknownResultType:
    """Marker type for uninitialized resilience context."""
    pass


UnknownResult = _UnknownResultType()


class ResiliencePropertyKey(Generic[TValue]):
    """Represents a strongly-typed key used by ResilienceProperties.

    Uses __slots__ to minimize memory allocations.
    """

    __slots__ = ("_key",)

    def __init__(self, key: str) -> None:
        if not key:
            raise ValueError("Key cannot be empty or None.")
        self._key = key

    @property
    def key(self) -> str:
        """Gets the key string."""
        return self._key

    def __str__(self) -> str:
        return self._key

    def __repr__(self) -> str:
        return f"ResiliencePropertyKey({self._key!r})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, ResiliencePropertyKey):
            return self._key == other._key
        return False

    def __hash__(self) -> int:
        return hash(self._key)


class ResilienceProperties:
    """Represents a collection of custom resilience properties."""

    __slots__ = ("_options",)

    def __init__(self) -> None:
        self._options: dict[str, Any] = {}

    @property
    def options(self) -> dict[str, Any]:
        """Gets the raw underlying dictionary."""
        return self._options

    def set(self, key: ResiliencePropertyKey[TValue], value: TValue) -> None:
        """Sets the property value for the specified key."""
        self._options[key.key] = value

    def try_get_value(self, key: ResiliencePropertyKey[TValue]) -> tuple[bool, TValue | None]:
        """Tries to get the property value for the specified key.

        Returns:
            A tuple of (found, value).
        """
        if key.key in self._options:
            val = self._options[key.key]
            return True, val
        return False, None

    def get_value(self, key: ResiliencePropertyKey[TValue], default_value: TValue) -> TValue:
        """Gets the property value for the key, or returns default_value if not found."""
        found, val = self.try_get_value(key)
        if found:
            return val  # type: ignore[return-value]
        return default_value

    def add_or_replace_properties(self, other: ResilienceProperties) -> None:
        """Copies all properties from other into this instance."""
        self._options.update(other._options)

    def clear(self) -> None:
        """Clears all properties."""
        self._options.clear()


class ResilienceContext:
    """A context assigned to a single execution of a ResiliencePipeline."""

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
        """Gets a value indicating whether the execution is synchronous."""
        return self._is_synchronous

    @property
    def result_type(self) -> Any:
        """Gets the result type associated with the execution."""
        return self._result_type

    @property
    def is_void(self) -> bool:
        """Gets a value indicating whether the execution represents a void result."""
        return self._result_type is VoidResult or self._result_type is _VoidResultType or self._result_type is None

    @property
    def is_initialized(self) -> bool:
        """Gets a value indicating whether the context has been initialized."""
        return self._result_type is not UnknownResult

    def initialize(self, result_type: Any, is_synchronous: bool) -> ResilienceContext:
        """Initializes the context for execution."""
        self._result_type = result_type
        self._is_synchronous = is_synchronous
        return self

    def initialize_from(self, source: ResilienceContext, cancellation_token: Any = None) -> None:
        """Initializes this context from another context."""
        self.operation_key = source.operation_key
        self._result_type = source.result_type
        self._is_synchronous = source.is_synchronous
        self.continue_on_captured_context = source.continue_on_captured_context
        self.cancellation_token = cancellation_token if cancellation_token is not None else source.cancellation_token
        self.properties.add_or_replace_properties(source.properties)

    def reset(self) -> bool:
        """Resets the context so it can be returned to the pool."""
        self.operation_key = None
        self.cancellation_token = None
        self.continue_on_captured_context = False
        self._is_synchronous = False
        self._result_type = UnknownResult
        self.properties.clear()
        return True


class ResilienceContextPool:
    """Thread-safe pool of ResilienceContext instances."""

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
        """Retrieves a ResilienceContext from the pool or creates a new one."""
        with self._lock:
            context = self._pool.pop() if self._pool else ResilienceContext()

        context.operation_key = operation_key
        context.cancellation_token = cancellation_token
        context.continue_on_captured_context = continue_on_captured_context
        return context

    def return_to_pool(self, context: ResilienceContext) -> None:
        """Returns a ResilienceContext back to the pool after execution."""
        if context is None:
            raise ValueError("Context cannot be None.")

        context.reset()
        with self._lock:
            if len(self._pool) < self._max_size:
                self._pool.append(context)


# Shared singleton pool
SharedResilienceContextPool = ResilienceContextPool()

