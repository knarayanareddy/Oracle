# ════════════════════════════════════════════════════════════════
# ORACLE Swarm Engine — Supabase Callback Writer (§11)
# Writes simulation rounds + final report to Supabase in real-time.
# Uses service role key via environment variable. NEVER expose to client.
# ════════════════════════════════════════════════════════════════
import os
import httpx
import json
from typing import Any


class SupabaseWriter:
    """Streams simulation results to Supabase tables in real-time."""

    def __init__(self):
        self.url = os.environ.get("SUPABASE_URL", "")
        self.key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
        self._headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        }

    @property
    def available(self) -> bool:
        return bool(self.url and self.key)

    def write_round(self, simulation_id: str, round_data: dict) -> None:
        """Write a single simulation round (broadcast over Realtime)."""
        if not self.available:
            return
        try:
            with httpx.Client(timeout=10) as client:
                client.post(
                    f"{self.url}/rest/v1/simulation_rounds",
                    json={"simulation_id": simulation_id, **round_data},
                    headers=self._headers,
                )
        except Exception as e:
            print(f"[SupabaseWriter] write_round error: {e}")

    def write_report(self, simulation_id: str, report: dict) -> None:
        """Write the final simulation report."""
        if not self.available:
            return
        try:
            with httpx.Client(timeout=10) as client:
                client.post(
                    f"{self.url}/rest/v1/simulation_reports",
                    json={"simulation_id": simulation_id, **report},
                    headers=self._headers,
                )
        except Exception as e:
            print(f"[SupabaseWriter] write_report error: {e}")

    def finalize_simulation(self, simulation_id: str, status: str, metrics: dict) -> None:
        """Update the simulation record with final status + metrics."""
        if not self.available:
            return
        try:
            with httpx.Client(timeout=10) as client:
                client.patch(
                    f"{self.url}/rest/v1/simulations?id=eq.{simulation_id}",
                    json={"status": status, **metrics},
                    headers=self._headers,
                )
        except Exception as e:
            print(f"[SupabaseWriter] finalize error: {e}")
