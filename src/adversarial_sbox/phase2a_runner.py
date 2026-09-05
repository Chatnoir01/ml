"""Execution gate and cell routing for Phase 2A neural qualification.

The module intentionally loads the committed classical panel lazily. Until
``phase2a_candidates.py`` exists, every neural execution path remains blocked.
"""

from __future__ import annotations

from typing import Any

from .phase2a_neural import CELL_SPECS


def _cell_spec(side: str, input_difference: int) -> tuple[str, int, int, str]:
    target = (str(side), int(input_difference))
    for spec in CELL_SPECS:
        if (spec[0], spec[2]) == target:
            return spec
    raise ValueError(f"undeclared Phase 2A cell {target!r}")


def load_committed_panel() -> tuple[dict[str, Any], ...]:
    """Load the frozen six-candidate panel, or fail closed before it exists."""

    try:
        from .phase2a_candidates import CANDIDATES, PANEL_DIGEST_SHA256
    except ImportError as exc:
        raise RuntimeError(
            "Phase 2A neural execution is blocked until phase2a_candidates.py is committed"
        ) from exc

    if len(CANDIDATES) != 6:
        raise RuntimeError("Phase 2A committed panel size mismatch")
    if not isinstance(PANEL_DIGEST_SHA256, str) or len(PANEL_DIGEST_SHA256) != 64:
        raise RuntimeError("Phase 2A committed panel digest is invalid")
    return tuple(dict(candidate) for candidate in CANDIDATES)
