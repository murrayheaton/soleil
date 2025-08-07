"""
Rate limiter for Google Drive API requests.

Implements a token bucket algorithm with configurable limits.
"""

import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Token bucket rate limiter with configurable limits.

    This rate limiter helps prevent API exhaustion by controlling the rate
    of requests to Google Drive API.
    """

    def __init__(
        self, requests_per_second: float = 10, burst_size: Optional[int] = None
    ):
        """
        Initialize the rate limiter.

        Args:
            requests_per_second: Maximum sustained request rate.
            burst_size: Maximum burst size (defaults to requests_per_second).
        """
        self.requests_per_second = requests_per_second
        self.burst_size = burst_size or requests_per_second
        self.tokens = float(self.burst_size)
        self.last_update = asyncio.get_event_loop().time()
        self.lock = asyncio.Lock()

        # Statistics
        self.total_requests = 0
        self.total_wait_time = 0.0
        self.rate_limit_hits = 0

    async def acquire(self, tokens: float = 1.0) -> float:
        """
        Acquire tokens from the bucket.

        Args:
            tokens: Number of tokens to acquire (default 1.0).

        Returns:
            The time waited (0 if no wait was necessary).
        """
        async with self.lock:
            now = asyncio.get_event_loop().time()
            time_passed = now - self.last_update

            # Refill tokens based on time passed
            self.tokens = min(
                self.burst_size,
                self.tokens + time_passed * self.requests_per_second,
            )
            self.last_update = now

            wait_time = 0.0
            if self.tokens >= tokens:
                self.tokens -= tokens
            else:
                # Calculate wait time needed
                tokens_needed = tokens - self.tokens
                wait_time = tokens_needed / self.requests_per_second

                logger.debug(f"Rate limit reached. Waiting {wait_time:.2f}s")
                self.rate_limit_hits += 1

                await asyncio.sleep(wait_time)

                # Update tokens after wait
                now = asyncio.get_event_loop().time()
                time_passed = now - self.last_update
                self.tokens = min(
                    self.burst_size,
                    self.tokens + time_passed * self.requests_per_second,
                )
                self.tokens -= tokens
                self.last_update = now

            self.total_requests += 1
            self.total_wait_time += wait_time

            return wait_time

    def get_stats(self) -> dict:
        """Get rate limiter statistics."""
        return {
            "total_requests": self.total_requests,
            "total_wait_time": self.total_wait_time,
            "rate_limit_hits": self.rate_limit_hits,
            "current_tokens": self.tokens,
            "requests_per_second": self.requests_per_second,
            "burst_size": self.burst_size,
        }

    def reset_stats(self) -> None:
        """Reset statistics."""
        self.total_requests = 0
        self.total_wait_time = 0.0
        self.rate_limit_hits = 0


class DynamicRateLimiter(RateLimiter):
    """
    Dynamic rate limiter that adjusts based on API responses.

    Automatically backs off when receiving rate limit errors and
    gradually increases rate when requests succeed.
    """

    def __init__(
        self,
        initial_requests_per_second: float = 10,
        min_requests_per_second: float = 1,
        max_requests_per_second: float = 100,
        backoff_factor: float = 0.5,
        recovery_factor: float = 1.1,
    ):
        """
        Initialize the dynamic rate limiter.

        Args:
            initial_requests_per_second: Starting request rate.
            min_requests_per_second: Minimum allowed rate.
            max_requests_per_second: Maximum allowed rate.
            backoff_factor: Factor to reduce rate on errors (0.5 = half).
            recovery_factor: Factor to increase rate on success (1.1 = 10% increase).
        """
        super().__init__(initial_requests_per_second)
        self.min_requests_per_second = min_requests_per_second
        self.max_requests_per_second = max_requests_per_second
        self.backoff_factor = backoff_factor
        self.recovery_factor = recovery_factor
        self.consecutive_successes = 0
        self.consecutive_failures = 0

    def report_success(self) -> None:
        """Report a successful request."""
        self.consecutive_successes += 1
        self.consecutive_failures = 0

        # Gradually increase rate after consecutive successes
        if self.consecutive_successes >= 10:
            new_rate = min(
                self.requests_per_second * self.recovery_factor,
                self.max_requests_per_second,
            )
            if new_rate > self.requests_per_second:
                logger.info(
                    f"Increasing rate limit from {self.requests_per_second:.1f} to {new_rate:.1f} requests/s"
                )
                self.requests_per_second = new_rate
                self.consecutive_successes = 0

    def report_rate_limit_error(self) -> None:
        """Report a rate limit error from the API."""
        self.consecutive_failures += 1
        self.consecutive_successes = 0

        # Back off immediately
        new_rate = max(
            self.requests_per_second * self.backoff_factor, self.min_requests_per_second
        )
        if new_rate < self.requests_per_second:
            logger.warning(
                f"Reducing rate limit from {self.requests_per_second:.1f} to {new_rate:.1f} requests/s"
            )
            self.requests_per_second = new_rate
