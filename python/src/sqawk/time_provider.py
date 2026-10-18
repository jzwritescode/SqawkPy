"""
TimeProvider abstraction module for resilience operations.

This module provides clock and delay abstractions (`TimeProvider`), including
a production system implementation (`SystemTimeProvider`) and a fully simulated
virtual implementation (`FakeTimeProvider`). This design ensures that all
time-dependent strategies (such as timeouts, backoffs, and circuit breaker
health windows) can be tested deterministically without real wall-clock sleeps.

Exports
-------
TimeProvider
    Abstract base class defining clock and delay capabilities.
SystemTimeProvider
    Standard production clock using `time.monotonic()` and `time.sleep()`.
FakeTimeProvider
    Deterministic virtual clock for unit and integration testing.
SystemTime
    Global singleton instance of `SystemTimeProvider`.
"""

from __future__ import annotations

import asyncio
import datetime
import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqawk.context import ResilienceContext


class TimeProvider(ABC):
    """
    Abstract base class providing time and delay abstractions for resilience strategies.

    Strategies use this interface instead of directly invoking system time or
    sleep APIs. This decoupling allows deterministic manipulation of time in tests.

    Notes
    -----
    Analogous to .NET 8's `System.TimeProvider`.
    """

    @abstractmethod
    def get_timestamp(self) -> float:
        """
        Get the current high-resolution monotonic timestamp in seconds.

        Returns
        -------
        float
            Current monotonic time in seconds.
        """
        ...

    def get_elapsed_time(self, starting_timestamp: float) -> float:
        """
        Calculate the elapsed duration in seconds since a starting timestamp.

        Parameters
        ----------
        starting_timestamp : float
            A timestamp previously returned by `get_timestamp()`.

        Returns
        -------
        float
            Duration in seconds elapsed since `starting_timestamp`.
        """
        # Calculate difference from current monotonic time
        return self.get_timestamp() - starting_timestamp

    @abstractmethod
    def get_utc_now(self) -> datetime.datetime:
        """
        Get the current date and time in UTC.

        Returns
        -------
        datetime.datetime
            Current UTC date and time with timezone information.
        """
        ...

    @abstractmethod
    def delay(self, seconds: float) -> None:
        """
        Synchronously delay execution for the specified duration in seconds.

        Parameters
        ----------
        seconds : float
            Duration in seconds to delay execution.
        """
        ...

    @abstractmethod
    async def delay_async(self, seconds: float) -> None:
        """
        Asynchronously delay execution for the specified duration in seconds.

        Parameters
        ----------
        seconds : float
            Duration in seconds to delay asynchronous execution.
        """
        ...

    async def delay_context(self, seconds: float, context: ResilienceContext) -> None:
        """
        Delay execution according to the context mode (synchronously or asynchronously).

        Parameters
        ----------
        seconds : float
            Duration in seconds to delay.
        context : ResilienceContext
            The active resilience context carrying execution mode flags.
        """
        # Non-positive delays require no waiting
        if seconds <= 0:
            return

        # Direct execution based on context mode
        if context.is_synchronous:
            self.delay(seconds)
        else:
            await self.delay_async(seconds)


class SystemTimeProvider(TimeProvider):
    """
    Production TimeProvider backed by the operating system clock and sleep calls.

    Uses `time.monotonic()` for monotonic timestamps, `datetime.datetime.now(timezone.utc)`
    for calendar timestamps, and standard library delays.
    """

    def get_timestamp(self) -> float:
        """
        Get the current system monotonic time.

        Returns
        -------
        float
            Monotonic seconds from system clock.
        """
        return time.monotonic()

    def get_utc_now(self) -> datetime.datetime:
        """
        Get current system UTC time.

        Returns
        -------
        datetime.datetime
            Current UTC time with timezone awareness.
        """
        return datetime.datetime.now(datetime.timezone.utc)

    def delay(self, seconds: float) -> None:
        """
        Synchronously block the calling thread for the specified duration.

        Parameters
        ----------
        seconds : float
            Duration in seconds to sleep.
        """
        if seconds > 0:
            time.sleep(seconds)

    async def delay_async(self, seconds: float) -> None:
        """
        Asynchronously yield control to the event loop for the specified duration.

        Parameters
        ----------
        seconds : float
            Duration in seconds to delay coroutine execution.
        """
        if seconds > 0:
            await asyncio.sleep(seconds)


class FakeTimeProvider(TimeProvider):
    """
    Simulated virtual TimeProvider for deterministic testing.

    Allows unit tests to fast-forward time instantly via `advance()` or auto-advance
    upon delay calls, eliminating real wall-clock waits.

    Parameters
    ----------
    start_time : datetime.datetime or None, optional
        The initial UTC time for the simulated clock (default is 2025-01-01T00:00:00Z).
    start_timestamp : float, optional
        The initial monotonic timestamp in seconds (default is 0.0).

    Attributes
    ----------
    total_delayed : float
        Sum of all seconds requested across all delay operations.
    delays : list of float
        Sequential list of all individual delay intervals recorded.
    """

    def __init__(
        self,
        start_time: datetime.datetime | None = None,
        start_timestamp: float = 0.0,
    ) -> None:
        # Initialize virtual UTC clock
        self._utc_now = start_time or datetime.datetime(2025, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
        # Initialize monotonic timestamp counter
        self._timestamp = start_timestamp
        # Record history of requested delays for assertion testing
        self._delay_history: list[float] = []

    def get_timestamp(self) -> float:
        """
        Get current virtual monotonic timestamp.

        Returns
        -------
        float
            Simulated monotonic seconds.
        """
        return self._timestamp

    def get_utc_now(self) -> datetime.datetime:
        """
        Get current virtual UTC date and time.

        Returns
        -------
        datetime.datetime
            Simulated UTC datetime.
        """
        return self._utc_now

    def advance(self, seconds: float) -> None:
        """
        Advance simulated time forward by the given duration in seconds.

        Parameters
        ----------
        seconds : float
            The duration in seconds to advance virtual time.

        Raises
        ------
        ValueError
            If `seconds` is negative.
        """
        if seconds < 0:
            raise ValueError("Cannot advance time backwards.")
        # Advance both monotonic timestamp and calendar time
        self._timestamp += seconds
        self._utc_now += datetime.timedelta(seconds=seconds)

    def set_utc_now(self, new_time: datetime.datetime) -> None:
        """
        Explicitly set the current virtual UTC time.

        Parameters
        ----------
        new_time : datetime.datetime
            The new virtual UTC datetime.
        """
        self._utc_now = new_time

    def delay(self, seconds: float) -> None:
        """
        Record delay duration and instantly advance virtual time without sleeping.

        Parameters
        ----------
        seconds : float
            Requested delay duration in seconds.
        """
        if seconds > 0:
            # Track delay request for test assertions
            self._delay_history.append(seconds)
            # Advance virtual time immediately to simulate elapsed delay
            self.advance(seconds)

    async def delay_async(self, seconds: float) -> None:
        """
        Record delay duration and instantly advance virtual time without awaiting real time.

        Parameters
        ----------
        seconds : float
            Requested delay duration in seconds.
        """
        if seconds > 0:
            # Track delay request for test assertions
            self._delay_history.append(seconds)
            # Advance virtual time immediately to simulate elapsed delay
            self.advance(seconds)

    @property
    def total_delayed(self) -> float:
        """
        Get the cumulative duration of all requested delays.

        Returns
        -------
        float
            Total delayed seconds.
        """
        return sum(self._delay_history)

    @property
    def delays(self) -> list[float]:
        """
        Get a copy of the list of all requested delay durations.

        Returns
        -------
        list of float
            Chronological list of delay durations in seconds.
        """
        return list(self._delay_history)


# Global shared production system clock instance
SystemTime = SystemTimeProvider()
