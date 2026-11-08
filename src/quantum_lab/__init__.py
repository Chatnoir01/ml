"""Simulation-only BB84 research lab, not a quantum network or key source."""

from .bb84 import BB84Config, simulate_bb84

__all__ = ["BB84Config", "simulate_bb84"]
