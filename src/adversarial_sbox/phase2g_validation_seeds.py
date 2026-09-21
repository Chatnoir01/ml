"""Physically isolated held-out H seed block for preregistered Phase 2G.

This module is post-freeze validation-only. Pre-H evolution, checkpoint training,
candidate scoring, terminal choice, and terminal freeze modules must not import it.
The values are the exact seeds frozen in issues #118/#119; no substitution or
runtime generation is permitted.
"""

from __future__ import annotations

HELDOUT_DATASET_SEEDS = (
    876003,
    876017,
    876029,
    876043,
    876057,
    876071,
    876083,
    876099,
)

HELDOUT_MODEL_SEEDS = (
    886007,
    886019,
    886031,
    886043,
    886061,
    886073,
    886091,
    886103,
)

HELDOUT_TRAININGS_PER_TERMINAL = 16
