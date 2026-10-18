"""
Outcome module for resilience operations.

This module provides the core `Outcome[TResult]` encapsulation type and the
`VoidResult` sentinel, which represent the outcome of executing a resilience
pipeline callback (either a returned value or a captured exception).

Exports
-------
Outcome
    Encapsulates a successful return value or a captured exception.
VoidResult
    Singleton sentinel representing an operation with no return value.
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

TResult = TypeVar("TResult")


class _VoidResultType:
    """
    Sentinel type representing an operation that completes without returning a value.

    This class implements a singleton pattern so that all void outcomes reference
    the identical sentinel instance.

    Notes
    -----
    Analogous to .NET Polly's `VoidResult` struct.
    """

    _instance: _VoidResultType | None = None

    def __new__(cls) -> _VoidResultType:
        """
        Create or return the singleton instance of _VoidResultType.

        Returns
        -------
        _VoidResultType
            The shared singleton instance.
        """
        if cls._instance is None:
            # Allocate singleton instance on first access
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        """
        Return the official string representation of the void result.

        Returns
        -------
        str
            The literal string "void".
        """
        return "void"

    def __str__(self) -> str:
        """
        Return the human-readable string representation of the void result.

        Returns
        -------
        str
            The literal string "void".
        """
        return "void"


# Global singleton instance for void operations
VoidResult = _VoidResultType()


class Outcome(Generic[TResult]):
    """
    Encapsulate the outcome of an operation as either a result or an exception.

    `Outcome` is the foundational return type for all resilience strategies,
    allowing strategies to intercept and evaluate outcomes without unwinding
    the call stack via exception propagation.

    Parameters
    ----------
    result : TResult or None, optional
        The successful result value, or None if the outcome represents a failure
        or void result (default is None).
    exception : BaseException or None, optional
        The captured exception, or None if the outcome represents a success
        (default is None).
    has_result : bool, optional
        Flag indicating whether this outcome represents a completed result
        rather than an exception (default is True).

    Attributes
    ----------
    result : TResult or None
        The operation result value, if successful.
    exception : BaseException or None
        The captured exception instance, if failed.
    has_result : bool
        True if the operation completed with a result; False if an exception occurred.
    is_void_result : bool
        True if the outcome encapsulates a `VoidResult`.

    Notes
    -----
    Uses `__slots__` to eliminate per-instance `__dict__` allocations on hot execution paths.
    """

    __slots__ = ("_result", "_exception", "_has_result")

    def __init__(
        self,
        result: TResult | None = None,
        exception: BaseException | None = None,
        *,
        has_result: bool = True,
    ) -> None:
        # Initialize internal slot storage directly
        self._result = result
        self._exception = exception
        self._has_result = has_result

    @property
    def result(self) -> TResult | None:
        """
        Get the result value of the operation.

        Returns
        -------
        TResult or None
            The result value if the operation succeeded, or None otherwise.
        """
        return self._result

    @property
    def exception(self) -> BaseException | None:
        """
        Get the exception captured during the operation.

        Returns
        -------
        BaseException or None
            The exception instance if the operation failed, or None otherwise.
        """
        return self._exception

    @property
    def has_result(self) -> bool:
        """
        Indicate whether the operation produced a result rather than an exception.

        Returns
        -------
        bool
            True if a result was produced (including void); False if an exception was captured.
        """
        return self._has_result

    @property
    def is_void_result(self) -> bool:
        """
        Indicate whether the operation produced a void result.

        Returns
        -------
        bool
            True if the encapsulated result is the VoidResult singleton; False otherwise.
        """
        return self._result is VoidResult

    def try_get_result(self) -> tuple[bool, TResult | None]:
        """
        Attempt to retrieve the result if available and non-void.

        Returns
        -------
        tuple of (bool, TResult or None)
            A tuple where the first element is True if a non-void result is available,
            and the second element is the result value.
        """
        # Ensure we only return True when a real, non-void value is present
        if self._has_result and not self.is_void_result:
            return True, self._result
        return False, None

    def throw_if_exception(self) -> None:
        """
        Rethrow the captured exception if the outcome encapsulates a failure.

        If the outcome represents a successful result, this method is a no-op.

        Raises
        ------
        BaseException
            The captured exception instance that caused the operation to fail.
        """
        # Propagate the original exception maintaining full traceback context
        if self._exception is not None:
            raise self._exception

    def get_result_or_rethrow(self) -> TResult:
        """
        Return the result value or raise the captured exception if the operation failed.

        Returns
        -------
        TResult
            The successful result of the operation.

        Raises
        ------
        BaseException
            The captured exception instance if the operation failed.
        """
        # If an exception was captured, rethrow it immediately
        if self._exception is not None:
            raise self._exception
        return self._result  # type: ignore[return-value]

    @classmethod
    def from_result(cls, value: TResult) -> Outcome[TResult]:
        """
        Create an Outcome instance encapsulating a successful result value.

        Parameters
        ----------
        value : TResult
            The successful operation value.

        Returns
        -------
        Outcome[TResult]
            An Outcome encapsulating the given result value.
        """
        return cls(result=value, exception=None, has_result=True)

    @classmethod
    def from_exception(cls, exception: BaseException) -> Outcome[Any]:
        """
        Create an Outcome instance encapsulating a captured exception.

        Parameters
        ----------
        exception : BaseException
            The exception instance to encapsulate.

        Returns
        -------
        Outcome[Any]
            An Outcome encapsulating the given exception.

        Raises
        ------
        ValueError
            If `exception` is None.
        """
        # Guard against invalid None exceptions
        if exception is None:
            raise ValueError("Exception cannot be None.")
        return cls(result=None, exception=exception, has_result=False)

    @classmethod
    def void(cls) -> Outcome[Any]:
        """
        Create an Outcome instance representing a successful void operation.

        Returns
        -------
        Outcome[Any]
            An Outcome encapsulating the VoidResult singleton.
        """
        return cls(result=VoidResult, exception=None, has_result=True)

    def __str__(self) -> str:
        """
        Return the string representation of the outcome.

        Returns
        -------
        str
            The exception message if failed; empty string if result is None;
            otherwise the string representation of the result.
        """
        if self._exception is not None:
            return str(self._exception)
        if self._result is None:
            return ""
        return str(self._result)

    def __repr__(self) -> str:
        """
        Return the debug representation of the outcome.

        Returns
        -------
        str
            Formatted debug string with result or exception details.
        """
        if self._has_result:
            return f"Outcome(result={self._result!r})"
        return f"Outcome(exception={self._exception!r})"
