"""
Unit tests for `Outcome[TResult]` and `VoidResult`.

These tests correspond directly to `Polly.Core.Tests/OutcomeTests.cs` in .NET Polly,
validating successful outcome wrapping, exception capture, void result semantics,
and string representation formatting.
"""

from __future__ import annotations

import pytest
from sqawk.outcome import Outcome, VoidResult


def test_ctor_result_ok() -> None:
    """Verify that Outcome.from_result correctly stores value and reports success."""
    # Create successful outcome with integer result
    outcome = Outcome.from_result(10)

    # Validate success flags and exception state
    assert outcome.has_result is True
    assert outcome.exception is None
    assert outcome.is_void_result is False

    # Verify try_get_result extraction
    success, result = outcome.try_get_result()
    assert success is True
    assert result == 10
    assert outcome.result == 10

    # Verify string representation converts value to string
    assert str(outcome) == "10"


def test_ctor_void_result_ok() -> None:
    """Verify that Outcome.void correctly represents void operations."""
    # Create void outcome instance
    outcome = Outcome.void()

    # Void operations count as successful results
    assert outcome.has_result is True
    assert outcome.exception is None
    assert outcome.is_void_result is True

    # try_get_result returns False for void results (no payload)
    success, result = outcome.try_get_result()
    assert success is False
    assert result is None
    assert outcome.result is VoidResult

    # Verify string formatting displays "void"
    assert str(outcome) == "void"


def test_ctor_exception_ok() -> None:
    """Verify that Outcome.from_exception correctly captures exception instances."""
    # Create failure outcome with an exception
    exc = RuntimeError("Dummy message.")
    outcome = Outcome.from_exception(exc)

    # Validate failure flags
    assert outcome.has_result is False
    assert outcome.exception is exc
    assert outcome.is_void_result is False

    # Failed outcomes return False for try_get_result
    success, result = outcome.try_get_result()
    assert success is False
    assert result is None

    # String representation displays exception message
    assert str(outcome) == "Dummy message."


def test_to_string_none_result_should_be_empty() -> None:
    """Verify that an Outcome containing None produces an empty string."""
    # None result should format as empty string matching Polly semantics
    outcome = Outcome.from_result(None)
    assert str(outcome) == ""


def test_ensure_success_result() -> None:
    """Verify that throw_if_exception is a no-op on successful outcomes."""
    # A successful outcome must not throw or raise
    outcome = Outcome.from_result("dummy")
    outcome.throw_if_exception()
    assert outcome.get_result_or_rethrow() == "dummy"


def test_ensure_success_exception() -> None:
    """Verify that throw_if_exception raises the encapsulated exception on failure."""
    # An exception outcome must raise the original exception
    exc = ValueError("Failed execution")
    outcome = Outcome.from_exception(exc)

    with pytest.raises(ValueError, match="Failed execution"):
        outcome.throw_if_exception()

    with pytest.raises(ValueError, match="Failed execution"):
        outcome.get_result_or_rethrow()


def test_from_exception_raises_if_none() -> None:
    """Verify that Outcome.from_exception rejects None arguments with ValueError."""
    # Null guard check
    with pytest.raises(ValueError, match="Exception cannot be None"):
        Outcome.from_exception(None)  # type: ignore[arg-type]
