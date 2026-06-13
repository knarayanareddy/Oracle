# ════════════════════════════════════════════════════════════════
# ORACLE API — Resilience Layer Tests
# Tests circuit breaker + retry_with_backoff + resilient_call.
# ════════════════════════════════════════════════════════════════
import sys
import os
import asyncio
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ── Circuit Breaker ──
@pytest.mark.asyncio
async def test_circuit_breaker_closed_passes():
    from services.resilience import CircuitBreaker, CircuitState
    cb = CircuitBreaker(name="test", failure_threshold=3)

    async def success():
        return "ok"

    result = await cb.call(success)
    assert result == "ok"
    assert cb.state == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_threshold():
    from services.resilience import CircuitBreaker, CircuitState

    cb = CircuitBreaker(name="test", failure_threshold=3, cooldown_seconds=60)

    async def fail():
        raise ConnectionError("service down")

    # Three failures should trip the breaker
    for _ in range(3):
        try:
            await cb.call(fail, fallback=lambda: "fallback")
        except ConnectionError:
            pass

    assert cb.state == CircuitState.OPEN


@pytest.mark.asyncio
async def test_circuit_breaker_fallback_when_open():
    from services.resilience import CircuitBreaker, CircuitState, CircuitOpenError

    cb = CircuitBreaker(name="test", failure_threshold=2, cooldown_seconds=60)

    async def fail():
        raise RuntimeError("down")

    # Trip the breaker
    await cb.call(fail, fallback=lambda: "fb")
    await cb.call(fail, fallback=lambda: "fb")
    assert cb.state == CircuitState.OPEN

    # Now it should fail-fast to fallback
    result = await cb.call(fail, fallback=lambda: "fast-fallback")
    assert result == "fast-fallback"


@pytest.mark.asyncio
async def test_circuit_breaker_raises_without_fallback():
    from services.resilience import CircuitBreaker, CircuitState, CircuitOpenError

    cb = CircuitBreaker(name="test", failure_threshold=2, cooldown_seconds=60)

    async def fail():
        raise RuntimeError("down")

    await cb.call(fail, fallback=lambda: "fb")
    await cb.call(fail, fallback=lambda: "fb")

    with pytest.raises(CircuitOpenError):
        await cb.call(fail)  # no fallback → should raise


@pytest.mark.asyncio
async def test_circuit_breaker_half_open_recovery():
    from services.resilience import CircuitBreaker, CircuitState

    cb = CircuitBreaker(name="test", failure_threshold=2, cooldown_seconds=0.1)

    call_count = {"n": 0}

    async def flaky():
        call_count["n"] += 1
        if call_count["n"] <= 2:
            raise RuntimeError("transient")
        return "recovered"

    # Trip the breaker
    await cb.call(flaky, fallback=lambda: "fb")
    await cb.call(flaky, fallback=lambda: "fb")
    assert cb.state == CircuitState.OPEN

    # Wait for cooldown
    await asyncio.sleep(0.15)

    # Should transition to HALF_OPEN, then CLOSED on success
    result = await cb.call(flaky, fallback=lambda: "fb")
    # After recovery success, circuit closes
    assert cb.state == CircuitState.CLOSED


# ── Retry with backoff ──
@pytest.mark.asyncio
async def test_retry_succeeds_after_transient_failure():
    from services.resilience import retry_with_backoff

    attempts = {"n": 0}

    async def flaky():
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise ConnectionError("rate limited")
        return "success"

    result = await retry_with_backoff(flaky, max_retries=3, base_delay=0.01)
    assert result == "success"
    assert attempts["n"] == 3


@pytest.mark.asyncio
async def test_retry_exhausted_raises():
    from services.resilience import retry_with_backoff

    async def always_fail():
        raise ConnectionError("permanently down")

    with pytest.raises(ConnectionError):
        await retry_with_backoff(always_fail, max_retries=2, base_delay=0.01)


# ── Resilient call (breaker + retry combined) ──
@pytest.mark.asyncio
async def test_resilient_call_uses_fallback_on_failure():
    from services.resilience import resilient_call, CircuitBreaker

    cb = CircuitBreaker(name="test", failure_threshold=10, cooldown_seconds=60)

    async def fail():
        raise RuntimeError("down")

    result = await resilient_call(fail, breaker=cb, fallback=lambda: "safe", max_retries=1, base_delay=0.01)
    assert result == "safe"


@pytest.mark.asyncio
async def test_resilient_call_passes_through_on_success():
    from services.resilience import resilient_call, CircuitBreaker

    cb = CircuitBreaker(name="test", failure_threshold=3)

    async def success():
        return "data"

    result = await resilient_call(success, breaker=cb, fallback=lambda: "fb", max_retries=1)
    assert result == "data"
