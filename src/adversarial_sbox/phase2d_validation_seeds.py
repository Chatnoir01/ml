"""Fresh held-out Phase 2D Block W seeds.

This module is intentionally separate from phase2d.py and the evolutionary runner.
No evolutionary module may import it. It is loaded only by provenance preflight,
terminal validation, and post-freeze aggregation.
"""

from __future__ import annotations

VALIDATION_DATASET_SEEDS = (
    476003,
    476017,
    476029,
    476043,
    476057,
    476071,
    476083,
    476099,
)
VALIDATION_MODEL_SEEDS = (
    486007,
    486019,
    486031,
    486043,
    486061,
    486073,
    486091,
    486103,
)

HELDOUT_REPLICATES = 8
HELDOUT_DIFFERENCE_COUNT = 2
HELDOUT_TRAININGS_PER_TERMINAL = HELDOUT_REPLICATES * HELDOUT_DIFFERENCE_COUNT
TERMINAL_COUNT = 36
TOTAL_HELDOUT_TRAININGS = TERMINAL_COUNT * HELDOUT_TRAININGS_PER_TERMINAL
