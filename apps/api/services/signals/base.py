# ════════════════════════════════════════════════════════════════
# Signal Pipeline Base (§13)
# Common interface for all signal layers.
# ════════════════════════════════════════════════════════════════
from abc import ABC, abstractmethod
from typing import Any


class SignalProvider(ABC):
    """Base class for L1-L5 signal providers."""

    layer: str = ""

    @abstractmethod
    async def fetch(self) -> list[dict]:
        """Return a list of signal event dicts matching signal_events schema."""
        ...
