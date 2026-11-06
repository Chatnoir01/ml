"""Phase 2I execution firewall.

This module intentionally contains no optimizer or training implementation.
It makes the future intervention phase fail closed until a frozen Phase-2H
result selects one preregistered mechanism family.
"""

from __future__ import annotations

from collections.abc import Mapping

SUPPORTED_MECHANISMS = ("H1", "H2", "H3", "H4")
INTERVENTION_FAMILIES = {
    "H1": "historical_replay_archive",
    "H2": "lagged_or_slow_target",
    "H3": "bounded_neural_influence",
    "H4": "partial_curriculum_retention",
}


def select_intervention_family(phase2h_result: Mapping[str, object]) -> str:
    """Select exactly one intervention family or fail closed.

    Phase 2I is deliberately not executable for ambiguous, missing, or multiple
    supported mechanisms. Combination designs require separate preregistration.
    """

    if str(phase2h_result.get("phase", "")) != "2H-result":
        raise ValueError("Phase-2I requires a frozen Phase-2H result")

    if not bool(phase2h_result.get("frozen", False)):
        raise ValueError("Phase-2H result is not frozen")

    supported_raw = phase2h_result.get("supported_mechanisms", ())
    if not isinstance(supported_raw, (list, tuple)):
        raise ValueError("Phase-2H supported mechanism list is malformed")
    supported = tuple(str(value) for value in supported_raw)

    unknown = sorted(set(supported) - set(SUPPORTED_MECHANISMS))
    if unknown:
        raise ValueError(f"unknown Phase-2H mechanisms: {unknown!r}")
    if len(supported) == 0:
        raise RuntimeError("Phase-2I rescue sweep forbidden: no supported mechanism")
    if len(supported) != 1:
        raise RuntimeError("Phase-2I combination intervention requires new preregistration")

    return INTERVENTION_FAMILIES[supported[0]]
