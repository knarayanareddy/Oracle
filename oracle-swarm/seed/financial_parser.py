# ════════════════════════════════════════════════════════════════
# ORACLE Swarm Engine — Financial Seed Parser (§11)
# Extracts: tickers, macro indicators, sentiment signals, event types,
# time horizons from financial text. Feeds into GraphRAG knowledge graph.
# ════════════════════════════════════════════════════════════════
import re
import json
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class FinancialEntities:
    tickers: list[str] = field(default_factory=list)
    macro_indicators: list[str] = field(default_factory=list)
    event_type: str = "other"
    sentiment_keywords: list[str] = field(default_factory=list)
    time_horizon: str = "medium"  # short, medium, long
    sectors_affected: list[str] = field(default_factory=list)
    confidence: float = 0.5


# Known patterns
TICKER_PATTERN = re.compile(r'\b[A-Z]{1,5}\b(?=\s|$|[,\.\)])')
MACRO_PATTERNS = {
    "interest_rate": re.compile(r'\b(rate|interest|fed funds|federal funds)\b', re.I),
    "inflation": re.compile(r'\b(inflation|CPI|PCE|price (?:level|index))\b', re.I),
    "employment": re.compile(r'\b(unemployment|jobs|labor|payroll|NFP)\b', re.I),
    "gdp": re.compile(r'\b(GDP|economic growth|recession)\b', re.I),
    "yield_curve": re.compile(r'\b(yield curve|treasury|bond yield|T10Y2Y)\b', re.I),
}
EVENT_PATTERNS = {
    "earnings": re.compile(r'\b(earnings|EPS|revenue|beat|miss|guidance)\b', re.I),
    "fed_statement": re.compile(r'\b(fed|federal reserve|powell|FOMC|rate (?:hike|cut|decision))\b', re.I),
    "macro": re.compile(r'\b(CPI|inflation|GDP|unemployment|recession)\b', re.I),
    "geopolitical": re.compile(r'\b(war|sanction|trade (?:war|tension)|geopolitical)\b', re.I),
}
SENTIMENT_MAP = {
    "bullish": ["beat", "surge", "rally", "growth", "strong", "record", "upgrade", "buyback", "boom"],
    "bearish": ["miss", "crash", "fear", "recession", "cut", "plunge", "warn", "downgrade", "weak"],
}
SECTOR_MAP = {
    "tech": ["NVDA", "AAPL", "MSFT", "GOOGL", "META", "AI", "semiconductor", "chip"],
    "financials": ["JPM", "bank", "financial"],
    "crypto": ["BTC", "ETH", "bitcoin", "crypto"],
    "bonds": ["TLT", "treasury", "bond", "yield"],
}
KNOWN_TICKERS = {
    "NVDA", "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "JPM",
    "SPY", "QQQ", "VTI", "BTC", "ETH", "TLT", "GLD", "VIX", "AMD",
    "NFLX", "BABA", "UBER", "COIN",
}


def parse_financial_seed(text: str) -> FinancialEntities:
    """Extract structured financial entities from a seed text."""
    entities = FinancialEntities()
    text_lower = text.lower()

    # Tickers
    matches = TICKER_PATTERN.findall(text)
    entities.tickers = [t for t in matches if t in KNOWN_TICKERS]

    # Macro indicators
    for label, pattern in MACRO_PATTERNS.items():
        if pattern.search(text):
            entities.macro_indicators.append(label)

    # Event type
    for event_type, pattern in EVENT_PATTERNS.items():
        if pattern.search(text):
            entities.event_type = event_type
            break

    # Sentiment keywords
    for direction, keywords in SENTIMENT_MAP.items():
        for kw in keywords:
            if kw in text_lower:
                entities.sentiment_keywords.append(f"{direction}:{kw}")

    # Time horizon
    if re.search(r'\b(today|this week|intraday|immediate)\b', text, re.I):
        entities.time_horizon = "short"
    elif re.search(r'\b(quarter|next year|2026|2027|long.?term)\b', text, re.I):
        entities.time_horizon = "long"

    # Sectors
    for sector, keywords in SECTOR_MAP.items():
        for kw in keywords:
            if kw.lower() in text_lower:
                entities.sectors_affected.append(sector)
                break

    # Confidence based on entity richness
    entity_count = len(entities.tickers) + len(entities.macro_indicators) + len(entities.sentiment_keywords)
    entities.confidence = min(0.95, 0.3 + entity_count * 0.12)

    return entities


def to_graphrag_nodes(entities: FinancialEntities, seed_text: str) -> list[dict]:
    """Convert extracted entities to GraphRAG knowledge graph nodes."""
    nodes = []
    for ticker in entities.tickers:
        nodes.append({"type": "asset", "label": ticker, "properties": {"source_seed": seed_text[:100]}})
    for macro in entities.macro_indicators:
        nodes.append({"type": "macro_indicator", "label": macro, "properties": {}})
    for sector in entities.sectors_affected:
        nodes.append({"type": "sector", "label": sector, "properties": {}})
    nodes.append({"type": "event", "label": entities.event_type, "properties": {"time_horizon": entities.time_horizon}})
    return nodes


if __name__ == "__main__":
    import sys
    seed = sys.argv[1] if len(sys.argv) > 1 else "Fed signals two rate hikes in 2026 as inflation proves sticky"
    result = parse_financial_seed(seed)
    print(json.dumps(asdict(result), indent=2))
    print("\nGraphRAG nodes:")
    print(json.dumps(to_graphrag_nodes(result, seed), indent=2))
