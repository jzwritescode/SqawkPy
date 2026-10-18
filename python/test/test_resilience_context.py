"""Tests for ResilienceContext and ResilienceProperties corresponding to dotnet tests."""

import pytest
from sqawk.context import (
    ResilienceContext,
    ResilienceContextPool,
    ResilienceProperties,
    ResiliencePropertyKey,
    SharedResilienceContextPool,
)
from sqawk.outcome import VoidResult


@pytest.mark.parametrize("synchronous", [True, False])
def test_initialize_typed_ok(synchronous: bool) -> None:
    context = SharedResilienceContextPool.get(cancellation_token="test-token")
    try:
        context.initialize(bool, synchronous)
        assert context.result_type is bool
        assert context.is_void is False
        assert context.is_initialized is True
        assert context.is_synchronous == synchronous
        assert context.continue_on_captured_context is False
        assert context.cancellation_token == "test-token"
    finally:
        SharedResilienceContextPool.return_to_pool(context)


@pytest.mark.parametrize("synchronous", [True, False])
def test_initialize_from_ok(synchronous: bool) -> None:
    context = SharedResilienceContextPool.get("some-key", cancellation_token="original-token")
    try:
        context.initialize(bool, synchronous)
        context.continue_on_captured_context = True
        key = ResiliencePropertyKey[str]("A")
        context.properties.set(key, "B")

        other = SharedResilienceContextPool.get()
        try:
            other.initialize_from(context, cancellation_token="new-token")
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
    context = SharedResilienceContextPool.get()
    try:
        context.initialize(VoidResult, synchronous)
        assert context.is_void is True
        assert context.is_initialized is True
        assert context.is_synchronous == synchronous
        assert context.continue_on_captured_context is False
    finally:
        SharedResilienceContextPool.return_to_pool(context)


def test_properties_try_get_value_ok() -> None:
    key = ResiliencePropertyKey[int]("dummy")
    props = ResilienceProperties()
    props.set(key, 12345)

    found, val = props.try_get_value(key)
    assert found is True
    assert val == 12345


def test_properties_try_get_value_none_ok() -> None:
    key = ResiliencePropertyKey[str | None]("dummy")
    props = ResilienceProperties()
    props.set(key, None)

    found, val = props.try_get_value(key)
    assert found is True
    assert val is None


def test_properties_try_get_value_not_found() -> None:
    key = ResiliencePropertyKey[int]("dummy")
    props = ResilienceProperties()

    found, val = props.try_get_value(key)
    assert found is False
    assert val is None


def test_properties_get_value_default() -> None:
    key = ResiliencePropertyKey[int]("dummy")
    props = ResilienceProperties()

    assert props.get_value(key, -1) == -1
    props.set(key, 999)
    assert props.get_value(key, -1) == 999


def test_properties_add_or_replace() -> None:
    key1 = ResiliencePropertyKey[str]("A")
    key2 = ResiliencePropertyKey[str]("B")

    props = ResilienceProperties()
    props.set(key1, "A_val")

    other = ResilienceProperties()
    other.set(key2, "B_val")

    props.add_or_replace_properties(other)
    assert len(props.options) == 2
    assert props.get_value(key1, "") == "A_val"
    assert props.get_value(key2, "") == "B_val"


def test_pool_reuse() -> None:
    pool = ResilienceContextPool(max_size=5)
    ctx1 = pool.get("op1")
    assert ctx1.operation_key == "op1"

    pool.return_to_pool(ctx1)
    assert ctx1.operation_key is None
    assert ctx1.is_initialized is False

    ctx2 = pool.get("op2")
    assert ctx2 is ctx1  # Reused from pool
    assert ctx2.operation_key == "op2"

