# ════════════════════════════════════════════════════════════════
# ORACLE Swarm Engine — Settings (§11)
# Offline mode flag for Phase 2 activation (ADR-009).
# ════════════════════════════════════════════════════════════════
import os

# Phase 2 activation point — no-op in Phase 1 (MVP)
OFFLINE_MODE = os.environ.get("ORACLE_OFFLINE_MODE", "false").lower() == "true"

# Simulation caps
MAX_AGENTS = int(os.environ.get("ORACLE_MAX_AGENTS", "1000"))
MAX_ROUNDS = int(os.environ.get("ORACLE_MAX_ROUNDS", "40"))

# Default agent mix (institutional, retail, media)
DEFAULT_AGENT_MIX = {"institutional": 35, "retail": 50, "media": 15}

# Default environments
DEFAULT_ENVIRONMENTS = ["twitter", "reddit"]

# LLM defaults
SIMULATION_LLM = os.environ.get("SIMULATION_LLM", "qwen-plus")
REASONING_LLM = os.environ.get("REASONING_LLM", "gpt-4o")
