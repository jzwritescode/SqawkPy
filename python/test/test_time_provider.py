"""
Unit tests for `TimeProvider`, `SystemTimeProvider`, and `FakeTimeProvider`.

These tests validate deterministic time progression, instant delay simulations,
UTC calendar calculations, and context-directed delay dispatching.
"""

from __future__ import annotations

import datetime
import pytest
from sqawk.context import SharedResilienceContextPool
from sqawk.time_provider import FakeTimeProvider, SystemTimeProvider


def test_fake_time_provider_advance() -> None:
    """Verify that FakeTimeProvider advances virtual timestamps and tracks elapsed time."""
    time_provider = FakeTimeProvider(start_timestamp=100.0)
    assert time_provider.get_timestamp() == 100.0

    # Advance virtual time by 5.5 seconds
    time_provider.advance(5.5)
    assert time_provider.get_timestamp() == 105.5
    assert time_provider.get_elapsed_time(100.0) == 5.5


def test_fake_time_provider_cannot_advance_backwards() -> None:
    """Verify that FakeTimeProvider rejects negative advance durations."""
    time_provider = FakeTimeProvider()
    with pytest.raises(ValueError, match="Cannot advance time backwards"):
        time_provider.advance(-1.0)


def test_fake_time_provider_delay_synchronous() -> None:
    """Verify that synchronous delay records duration and advances simulated time."""
    time_provider = FakeTimeProvider(start_timestamp=0.0)

    # Trigger synchronous delay
    time_provider.delay(10.0)

    # Virtual clock must advance instantly without actual sleeping
    assert time_provider.get_timestamp() == 10.0
    assert time_provider.total_delayed == 10.0
    assert time_provider.delays == [10.0]


@pytest.mark.asyncio
async def test_fake_time_provider_delay_asynchronous() -> None:
    """Verify that asynchronous delay records duration and advances simulated time."""
    time_provider = FakeTimeProvider(start_timestamp=0.0)

    # Trigger asynchronous delay
    await time_provider.delay_async(2.5)

    # Virtual clock must advance instantly
    assert time_provider.get_timestamp() == 2.5
    assert time_provider.total_delayed == 2.5
    assert time_provider.delays == [2.5]


@pytest.mark.asyncio
async def test_fake_time_provider_delay_context() -> None:
    """Verify that delay_context dispatches correctly for sync and async execution contexts."""
    time_provider = FakeTimeProvider(start_timestamp=0.0)

    # Test synchronous context execution
    ctx_sync = SharedResilienceContextPool.get()
    ctx_sync.initialize(int, is_synchronous=True)
    try:
        await time_provider.delay_context(3.0, ctx_sync)
        assert time_provider.get_timestamp() == 3.0
    finally:
        SharedResilienceContextPool.return_to_pool(ctx_sync)

    # Test asynchronous context execution
    ctx_async = SharedResilienceContextPool.get()
    ctx_async.initialize(int, is_synchronous=False)
    try:
        await time_provider.delay_context(4.0, ctx_async)
        assert time_provider.get_timestamp() == 7.0
    finally:
        SharedResilienceContextPool.return_to_pool(ctx_async)


def test_fake_time_provider_utc_now() -> None:
    """Verify that FakeTimeProvider calculates virtual UTC datetime offsets accurately."""
    start = datetime.datetime(2025, 6, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
    time_provider = FakeTimeProvider(start_time=start)
    assert time_provider.get_utc_now() == start

    # Advance 1 hour (3600 seconds)
    time_provider.advance(3600.0)
    assert time_provider.get_utc_now() == start + datetime.timedelta(hours=1)


def test_system_time_provider() -> None:
    """Verify that SystemTimeProvider returns monotonic time and valid UTC timestamps."""
    provider = SystemTimeProvider()
    t1 = provider.get_timestamp()
    t2 = provider.get_timestamp()

    # Monotonic time must not run backwards
    assert t2 >= t1

    # UTC datetime must include timezone info
    now = provider.get_utc_now()
    assert now.tzinfo is not None
