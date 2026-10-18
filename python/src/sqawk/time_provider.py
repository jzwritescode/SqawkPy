"""TimeProvider abstraction for deterministic, controllable time in resilience pipelines."""

from __future__ import annotations

import asyncio
import datetime
import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sqawk.context import ResilienceContext


class TimeProvider(ABC):
    """Abstract base class for system and simulated clocks."""

    @abstractmethod
    def get_timestamp(self) -> float:
        """Gets current high-resolution monotonic timestamp in seconds."""
        ...

    def get_elapsed_time(self, starting_timestamp: float) -> float:
        """Calculates elapsed time in seconds since starting_timestamp."""
        return self.get_timestamp() - starting_timestamp

    @abstractmethod
    def get_utc_now(self) -> datetime.datetime:
        """Gets current UTC date and time."""
        ...

    @abstractmethod
    def delay(self, seconds: float) -> None:
        """Synchronously delays execution for the specified number of seconds."""
        ...

    @abstractmethod
    async def delay_async(self, seconds: float) -> None:
        """Asynchronously delays execution for the specified number of seconds."""
        ...

    async def delay_context(self, seconds: float, context: ResilienceContext) -> None:
        """Delays execution according to the context (synchronously or asynchronously)."""
        if seconds <= 0:
            return

        if context.is_synchronous:
            self.delay(seconds)
        else:
            await self.delay_async(seconds)


class SystemTimeProvider(TimeProvider):
    """Production TimeProvider using real system clock and delays."""

    def get_timestamp(self) -> float:
        return time.monotonic()

    def get_utc_now(self) -> datetime.datetime:
        return datetime.datetime.now(datetime.timezone.utc)

    def delay(self, seconds: float) -> None:
        if seconds > 0:
            time.sleep(seconds)

    async def delay_async(self, seconds: float) -> None:
        if seconds > 0:
            await asyncio.sleep(seconds)


class FakeTimeProvider(TimeProvider):
    """Simulated TimeProvider for deterministic testing without real wall-clock delays."""

    def __init__(
        self,
        start_time: datetime.datetime | None = None,
        start_timestamp: float = 0.0,
    ) -> None:
        self._utc_now = start_time or datetime.datetime(2025, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
        self._timestamp = start_timestamp
        self._delay_history: list[float] = []

    def get_timestamp(self) -> float:
        return self._timestamp

    def get_utc_now(self) -> datetime.datetime:
        return self._utc_now

    def advance(self, seconds: float) -> None:
        """Advances simulated time by the given duration in seconds."""
        if seconds < 0:
            raise ValueError("Cannot advance time backwards.")
        self._timestamp += seconds
        self._utc_now += datetime.timedelta(seconds=seconds)

    def set_utc_now(self, new_time: datetime.datetime) -> None:
        """Sets the current simulated UTC time."""
        self._utc_now = new_time

    def delay(self, seconds: float) -> None:
        """Records delay and immediately advances simulated time without real waiting."""
        if seconds > 0:
            self._delay_history.append(seconds)
            self.advance(seconds)

    async def delay_async(self, seconds: float) -> None:
        """Records delay and immediately advances simulated time without real waiting."""
        if seconds > 0:
            self._delay_history.append(seconds)
            self.advance(seconds)

    @property
    def total_delayed(self) -> float:
        """Gets total seconds requested for delays."""
        return sum(self._delay_history)

    @property
    def delays(self) -> list[float]:
        """Gets list of individual delay durations requested."""
        return list(self._delay_history)


# Shared system time provider singleton
SystemTime = SystemTimeProvider()

