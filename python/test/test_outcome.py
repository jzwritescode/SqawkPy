"""Tests for Outcome[TResult] corresponding to dotnet OutcomeTests."""

import pytest
from sqawk.outcome import Outcome, VoidResult


def test_ctor_result_ok() -> None:
    outcome = Outcome.from_result(10)
    assert outcome.has_result is True
    assert outcome.exception is None
    assert outcome.is_void_result is False

    success, result = outcome.try_get_result()
    assert success is True
    assert result == 10
    assert outcome.result == 10
    assert str(outcome) == "10"


def test_ctor_void_result_ok() -> None:
    outcome = Outcome.void()
    assert outcome.has_result is True
    assert outcome.exception is None
    assert outcome.is_void_result is True

    success, result = outcome.try_get_result()
    assert success is False
    assert result is None
    assert outcome.result is VoidResult
    assert str(outcome) == "void"


def test_ctor_exception_ok() -> None:
    exc = RuntimeError("Dummy message.")
    outcome = Outcome.from_exception(exc)
    assert outcome.has_result is False
    assert outcome.exception is exc
    assert outcome.is_void_result is False

    success, result = outcome.try_get_result()
    assert success is False
    assert result is None
    assert str(outcome) == "Dummy message."


def test_to_string_none_result_should_be_empty() -> None:
    outcome = Outcome.from_result(None)
    assert str(outcome) == ""


def test_ensure_success_result() -> None:
    outcome = Outcome.from_result("dummy")
    # Should not raise
    outcome.throw_if_exception()
    assert outcome.get_result_or_rethrow() == "dummy"


def test_ensure_success_exception() -> None:
    exc = ValueError("Failed execution")
    outcome = Outcome.from_exception(exc)

    with pytest.raises(ValueError, match="Failed execution"):
        outcome.throw_if_exception()

    with pytest.raises(ValueError, match="Failed execution"):
        outcome.get_result_or_rethrow()


def test_from_exception_raises_if_none() -> None:
    with pytest.raises(ValueError, match="Exception cannot be None"):
        Outcome.from_exception(None)  # type: ignore[arg-type]

