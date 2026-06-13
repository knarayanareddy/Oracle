# ════════════════════════════════════════════════════════════════
# ORACLE Swarm Engine — Cost Tracker (§11)
# Tracks tokens per model per run, writes to simulation cost_usd field.
# ════════════════════════════════════════════════════════════════
from dataclasses import dataclass, field

# Pricing per 1K tokens (USD) — update from provider docs
PRICING = {
    "gpt-4o": {"input": 0.0025, "output": 0.01},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "qwen-plus": {"input": 0.0004, "output": 0.0012},
    "qwen-turbo": {"input": 0.00005, "output": 0.0002},
}


@dataclass
class CostTracker:
    """Tracks token usage and cost per simulation run."""
    model: str = "gpt-4o-mini"
    input_tokens: int = 0
    output_tokens: int = 0

    def add_input(self, tokens: int) -> None:
        self.input_tokens += tokens

    def add_output(self, tokens: int) -> None:
        self.output_tokens += tokens

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def cost_usd(self) -> float:
        pricing = PRICING.get(self.model, PRICING["gpt-4o-mini"])
        cost = (self.input_tokens / 1000 * pricing["input"]) + (self.output_tokens / 1000 * pricing["output"])
        return round(cost, 4)

    def to_dict(self) -> dict:
        return {
            "model": self.model,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "cost_usd": self.cost_usd,
        }
