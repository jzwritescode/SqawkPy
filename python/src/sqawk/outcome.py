"""Represents the outcome of an operation (result or exception)."""

from __future__ import annotations

import sys
from typing import Any, Generic, TypeVar

TResult = TypeVar("TResult")


class _VoidResultType:
    """Sentinel type representing a void operation result."""

    _instance: _VoidResultType | None = None

    def __new__(cls) -> _VoidResultType:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "void"

    def __str__(self) -> str:
        return "void"


VoidResult = _VoidResultType()


class Outcome(Generic[TResult]):
    """Represents the outcome of an operation which could be a result or an exception.

    Uses __slots__ to minimize memory allocations on hot execution paths.
    """

    __slots__ = ("_result", "_exception", "_has_result")

    def __init__(
        self,
        result: TResult | None = None,
        exception: BaseException | None = None,
        *,
        has_result: bool = True,
    ) -> None:
        self._result = result
        self._exception = exception
        self._has_result = has_result

    @property
    def result(self) -> TResult | None:
        """Gets the result of the operation, if any."""
        return self._result

    @property
    def exception(self) -> BaseException | None:
        """Gets the exception that occurred during the operation, if any."""
        return self._exception

    @property
    def has_result(self) -> bool:
        """Gets a value indicating whether the operation produced a result."""
        return self._has_result

    @property
    def is_void_result(self) -> bool:
        """Gets a value indicating whether the operation produced a void result."""
        return self._result is VoidResult

    def try_get_result(self) -> tuple[bool, TResult | None]:
        """Tries to get the result if available.

        Returns:
            A tuple of (success, result).
        """
        if self._has_result and not self.is_void_result:
            return True, self._result
        return False, None

    def throw_if_exception(self) -> None:
        """Raises the exception if the outcome encapsulates an exception.

        If the outcome represents a result, does nothing.
        """
        if self._exception is not None:
            raise self._exception

    def get_result_or_rethrow(self) -> TResult:
        """Returns the result if successful, or raises the captured exception."""
        if self._exception is not None:
            raise self._exception
        return self._result  # type: ignore[return-value]

    @classmethod
    def from_result(cls, value: TResult) -> Outcome[TResult]:
        """Creates an Outcome encapsulating a successful result."""
        return cls(result=value, exception=None, has_result=True)

    @classmethod
    def from_exception(cls, exception: BaseException) -> Outcome[Any]:
        """Creates an Outcome encapsulating an exception."""
        if exception is None:
            raise ValueError("Exception cannot be None.")
        return cls(result=None, exception=exception, has_result=False)

    @classmethod
    def void(cls) -> Outcome[Any]:
        """Creates an Outcome representing a void result."""
        return cls(result=VoidResult, exception=None, has_result=True)

    def __str__(self) -> str:
        if self._exception is not None:
            return str(self._exception)
        if self._result is None:
            return ""
        return str(self._result)

    def __repr__(self) -> str:
        if self._has_result:
            return f"Outcome(result={self._result!r})"
        return f"Outcome(exception={self._exception!r})"

