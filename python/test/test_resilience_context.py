"""
Unit tests for `ResilienceContext`, `ResilienceProperties`, and `ResilienceContextPool`.

These tests correspond directly to `Polly.Core.Tests/ResilienceContextTests.cs` and
`Polly.Core.Tests/ResiliencePropertiesTests.cs` in .NET Polly, verifying typed
property retrieval, context initialization, context copying, and pool reuse.
"""

from __future__ import annotations

import pytest
from sqawk.context import (
    ResilienceContextPool,
    ResilienceProperties,
    ResiliencePropertyKey,
    SharedResilienceContextPool,
)
from sqawk.outcome import VoidResult


@pytest.mark.parametrize("synchronous", [True, False])
def test_initialize_typed_ok(synchronous: bool) -> None:
    """Verify that ResilienceContext initializes with a typed result and execution mode."""
    # Lease context from shared pool
    context = SharedResilienceContextPool.get(cancellation_token="test-token")
    try:
        # Initialize context for bool result type and given sync/async mode
        context.initialize(bool, synchronous)

        # Assert context fields match initialization arguments
        assert context.result_type is bool
        assert context.is_void is False
        assert context.is_initialized is True
        assert context.is_synchronous == synchronous
        assert context.continue_on_captured_context is False
        assert context.cancellation_token == "test-token"
    finally:
        # Guarantee context is returned to pool to prevent leaks
        SharedResilienceContextPool.return_to_pool(context)


@pytest.mark.parametrize("synchronous", [True, False])
def test_initialize_from_ok(synchronous: bool) -> None:
    """Verify that initialize_from copies all metadata and properties from a source context."""
    # Create source context with operation key and custom properties
    context = SharedResilienceContextPool.get("some-key", cancellation_token="original-token")
    try:
        context.initialize(bool, synchronous)
        context.continue_on_captured_context = True
        key = ResiliencePropertyKey[str]("A")
        context.properties.set(key, "B")

        # Lease destination context
        other = SharedResilienceContextPool.get()
        try:
            # Copy state while overriding cancellation token
            other.initialize_from(context, cancellation_token="new-token")

            # Validate copied properties and overridden cancellation token
            assert other.result_type is bool
            assert other.is_void is False
            assert other.is_initialized is True
            assert other.is_synchronous == synchronous
            assert other.continue_on_captured_context is True
            assert other.operation_key == "some-key"
            assert other.cancellation_token == "new-token"
            assert other.properties.get_value(key, "") == "B"
        finally:
            SharedResilienceContextPool.return_to_pool(other)
    finally:
        SharedResilienceContextPool.return_to_pool(context)


@pytest.mark.parametrize("synchronous", [True, False])
def test_initialize_void_ok(synchronous: bool) -> None:
    """Verify that ResilienceContext properly reflects void operations."""
    context = SharedResilienceContextPool.get()
    try:
        # Initialize context for void result type
        context.initialize(VoidResult, synchronous)

        # is_void must evaluate to True for VoidResult sentinel
        assert context.is_void is True
        assert context.is_initialized is True
        assert context.is_synchronous == synchronous
        assert context.continue_on_captured_context is False
    finally:
        SharedResilienceContextPool.return_to_pool(context)


def test_properties_try_get_value_ok() -> None:
    """Verify that ResilienceProperties successfully retrieves a set typed value."""
    key = ResiliencePropertyKey[int]("dummy")
    props = ResilienceProperties()
    props.set(key, 12345)

    # Key lookup must find the value
    found, val = props.try_get_value(key)
    assert found is True
    assert val == 12345


def test_properties_try_get_value_none_ok() -> None:
    """Verify that ResilienceProperties can store and retrieve None as a valid value."""
    key = ResiliencePropertyKey[str | None]("dummy")
    props = ResilienceProperties()
    props.set(key, None)

    # Must return True for existence even when stored value is None
    found, val = props.try_get_value(key)
    assert found is True
    assert val is None


def test_properties_try_get_value_not_found() -> None:
    """Verify that try_get_value returns False when a key does not exist."""
    key = ResiliencePropertyKey[int]("dummy")
    props = ResilienceProperties()

    found, val = props.try_get_value(key)
    assert found is False
    assert val is None


def test_properties_get_value_default() -> None:
    """Verify that get_value falls back to default_value when key is missing."""
    key = ResiliencePropertyKey[int]("dummy")
    props = ResilienceProperties()

    # Returns fallback default when missing
    assert props.get_value(key, -1) == -1

    # Returns stored value when present
    props.set(key, 999)
    assert props.get_value(key, -1) == 999


def test_properties_add_or_replace() -> None:
    """Verify that add_or_replace_properties merges entries from another collection."""
    key1 = ResiliencePropertyKey[str]("A")
    key2 = ResiliencePropertyKey[str]("B")

    props = ResilienceProperties()
    props.set(key1, "A_val")

    other = ResilienceProperties()
    other.set(key2, "B_val")

    # Merge properties from other into props
    props.add_or_replace_properties(other)
    assert len(props.options) == 2
    assert props.get_value(key1, "") == "A_val"
    assert props.get_value(key2, "") == "B_val"


def test_pool_reuse() -> None:
    """Verify that ResilienceContextPool recycles context instances and clears state."""
    pool = ResilienceContextPool(max_size=5)

    # Lease first context
    ctx1 = pool.get("op1")
    assert ctx1.operation_key == "op1"

    # Return to pool, verifying state reset
    pool.return_to_pool(ctx1)
    assert ctx1.operation_key is None
    assert ctx1.is_initialized is False

    # Lease again - should pop the recycled instance
    ctx2 = pool.get("op2")
    assert ctx2 is ctx1  # Identity check: reused object from pool
    assert ctx2.operation_key == "op2"
