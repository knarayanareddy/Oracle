# ════════════════════════════════════════════════════════════════
# ORACLE — Resilience Layer
# Circuit breaker + exponential backoff retry for LLM calls,
# market data, and external APIs. Prevents cascading failures
# and abrupt quality drops during live demos.
#
# Addresses expert feedback: "robust retry logic and circuit breakers
# for LLM calls (LangChain)" + "Rate Limits and Fallbacks"
# ════════════════════════════════════════════════════════════════
import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Awaitable, Callable, TypeVar
from functools import wraps

from logging_config import logger

T = TypeVar("T")


class CircuitState(str, Enum):
    CLOSED = "closed"      # normal operation, requests flow through
    OPEN = "open"          # tripped — requests fail-fast, no downstream call
    HALF_OPEN = "half_open"  # testing if downstream recovered


@dataclass
class CircuitBreaker:
    """
    Circuit breaker pattern for external service calls.

    States:
      CLOSED    → requests pass; failures counted
      OPEN      → requests fail-fast immediately (cooldown)
      HALF_OPEN → limited probe request to test recovery

    Prevents the "abrupt shift to mock debate" scenario during a live
    demo by keeping the breaker OPEN for a cooldown rather than letting
    every request fall through to fallback.
    """
    name: str
    failure_threshold: int = 5
    cooldown_seconds: float = 30.0
    half_open_max_calls: int = 1
    _state: CircuitState = CircuitState.CLOSED
    _failure_count: int = 0
    _success_count: int = 0
    _last_failure_time: float = 0.0
    _half_open_calls: int = 0
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False)

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN:
            # Check if cooldown elapsed → transition to HALF_OPEN
            if time.monotonic() - self._last_failure_time >= self.cooldown_seconds:
                self._state = CircuitState.HALF_OPEN
                self._half_open_calls = 0
                logger.info("circuit_breaker_half_open", name=self.name)
        return self._state

    async def call(self, fn: Callable[[], Awaitable[T]], fallback: Callable[[], T] | None = None) -> T:
        """
        Execute an async callable through the circuit breaker.

        Args:
            fn: The async function to call (e.g. an LLM invocation).
            fallback: Called when circuit is OPEN or all retries exhausted.
                      If None and circuit trips, raises CircuitOpenError.
        """
        async with self._lock:
            current = self.state
            if current == CircuitState.OPEN:
                logger.warning("circuit_breaker_open_fallback", name=self.name)
                if fallback is not None:
                    return fallback()
                raise CircuitOpenError(f"Circuit '{self.name}' is OPEN")
            if current == CircuitState.HALF_OPEN and self._half_open_calls >= self.half_open_max_calls:
                if fallback is not None:
                    return fallback()
                raise CircuitOpenError(f"Circuit '{self.name}' is OPEN (half-open limited)")

            if current == CircuitState.HALF_OPEN:
                self._half_open_calls += 1

        # Execute outside lock to allow concurrency when CLOSED
        try:
            result = await fn()
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            if fallback is not None:
                logger.warning(
                    "circuit_breaker_fallback_used",
                    name=self.name,
                    error=str(e),
                    state=self.state,
                )
                return fallback()
            raise

    async def _on_success(self) -> None:
        async with self._lock:
            self._success_count += 1
            if self._state == CircuitState.HALF_OPEN:
                # Recovered
                self._state = CircuitState.CLOSED
                self._failure_count = 0
                logger.info("circuit_breaker_recovered", name=self.name)

    async def _on_failure(self) -> None:
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.monotonic()
            if self._state == CircuitState.HALF_OPEN:
                # Probe failed — back to OPEN
                self._state = CircuitState.OPEN
                logger.warning("circuit_breaker_reopened", name=self.name)
            elif self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                logger.warning(
                    "circuit_breaker_tripped",
                    name=self.name,
                    failures=self._failure_count,
                    threshold=self.failure_threshold,
                )

    def reset(self) -> None:
        """Manually reset (useful in tests)."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._half_open_calls = 0


class CircuitOpenError(Exception):
    """Raised when circuit is OPEN and no fallback provided."""


# ════════════════════════════════════════════════════════════════
# Exponential Backoff Retry
# ════════════════════════════════════════════════════════════════
async def retry_with_backoff(
    fn: Callable[[], Awaitable[T]],
    *,
    max_retries: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 8.0,
    retryable_exceptions: tuple = (Exception,),
) -> T:
    """
    Retry an async callable with exponential backoff + jitter.

    Delay sequence: base_delay * 2^attempt + random jitter, capped at max_delay.
    Designed for transient failures (rate limits 429, timeouts, 5xx).
    """
    import random
    last_exc: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            return await fn()
        except retryable_exceptions as e:
            last_exc = e
            if attempt == max_retries:
                logger.warning("retry_exhausted", attempts=attempt + 1, error=str(e))
                raise
            delay = min(base_delay * (2 ** attempt), max_delay)
            delay += random.uniform(0, 0.25)  # jitter to avoid thundering herd
            logger.info("retry_attempt", attempt=attempt + 1, delay=round(delay, 2), error=str(e))
            await asyncio.sleep(delay)
    assert last_exc is not None
    raise last_exc


# ════════════════════════════════════════════════════════════════
# Combined: Circuit Breaker + Retry (the recommended pattern)
# ════════════════════════════════════════════════════════════════
async def resilient_call(
    fn: Callable[[], Awaitable[T]],
    *,
    breaker: CircuitBreaker,
    fallback: Callable[[], T] | None = None,
    max_retries: int = 2,
    base_delay: float = 0.5,
) -> T:
    """
    Wrap a call in retry-with-backoff INSIDE a circuit breaker.

    Flow:
      1. Circuit OPEN? → return fallback immediately (no call made)
      2. Circuit CLOSED/HALF_OPEN → retry with backoff up to max_retries
      3. All retries fail → register failure with breaker → return fallback

    This is the correct layering: retries handle transient blips,
    circuit breaker handles sustained outages.
    """

    async def retried() -> T:
        return await retry_with_backoff(fn, max_retries=max_retries, base_delay=base_delay)

    return await breaker.call(retried, fallback=fallback)


# ════════════════════════════════════════════════════════════════
# Shared circuit breakers (singletons)
# ════════════════════════════════════════════════════════════════

# LLM calls (OpenAI / Qwen) — 429 rate limits, 5xx, timeouts
llm_breaker = CircuitBreaker(
    name="llm",
    failure_threshold=5,
    cooldown_seconds=30.0,
)

# Market data (yfinance / Alpha Vantage / Polygon) — rate limits
market_data_breaker = CircuitBreaker(
    name="market_data",
    failure_threshold=4,
    cooldown_seconds=20.0,
)

# Polymarket API
polymarket_breaker = CircuitBreaker(
    name="polymarket",
    failure_threshold=3,
    cooldown_seconds=45.0,
)

# News API
news_breaker = CircuitBreaker(
    name="news",
    failure_threshold=3,
    cooldown_seconds=60.0,
)
