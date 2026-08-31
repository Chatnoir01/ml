"""Central seed registry for Phase-1 experiments.

A confirmatory seed becomes retired forever after first use. Development code may
never use a confirmatory or retired seed. The registry also documents one
historical overlap discovered after two concurrent research branches were merged.
"""

from __future__ import annotations

BASELINE_SEEDS = frozenset({11, 23, 37, 53, 71})
DEV_V1_SEEDS = frozenset({101, 103, 107})

# First confirmatory experiment already present on main.
CONFIRM_V1_SEEDS = frozenset(
    {131, 137, 149, 157, 163, 173, 181, 191, 197, 211, 223, 227}
)

# Historical strict comparison run on a concurrent branch. 211/223/227 overlap
# CONFIRM_V1 and therefore that run must not be described as fully blind.
STRICT_HISTORICAL_SEEDS = frozenset({211, 223, 227, 229, 233, 239, 241, 251, 257})

# Phase-1B V2 development and confirmation seeds are permanently consumed.
DEV_V2_SEEDS = (307, 311, 313, 317, 331)
CONFIRM_V2_RESERVED_SEEDS = (401, 409, 419, 421, 431, 433, 439, 443, 449)
CONFIRM_V2_USED_SEEDS = frozenset(CONFIRM_V2_RESERVED_SEEDS)

USED_BEFORE_V2 = (
    BASELINE_SEEDS
    | DEV_V1_SEEDS
    | CONFIRM_V1_SEEDS
    | STRICT_HISTORICAL_SEEDS
)

# Fresh Phase-1C V3 development seeds, fixed before V3 algorithm results exist.
DEV_V3_SEEDS = (503, 509, 521, 523, 541)

# V3 confirmation seeds reserved before development and forbidden to tuning code.
CONFIRM_V3_RESERVED_SEEDS = (601, 607, 613, 617, 619, 631, 641, 643, 647)

USED_BEFORE_V3 = (
    USED_BEFORE_V2
    | set(DEV_V2_SEEDS)
    | CONFIRM_V2_USED_SEEDS
)


def validate_seed_registry() -> None:
    """Raise if development/confirmation isolation is violated."""

    dev_v2 = set(DEV_V2_SEEDS)
    confirm_v2 = set(CONFIRM_V2_RESERVED_SEEDS)
    if dev_v2 & USED_BEFORE_V2:
        raise ValueError("DEV_V2_SEEDS overlap an already-used seed")
    if confirm_v2 & USED_BEFORE_V2:
        raise ValueError("CONFIRM_V2_RESERVED_SEEDS overlap an already-used seed")
    if dev_v2 & confirm_v2:
        raise ValueError("V2 development and confirmation seeds overlap")

    dev_v3 = set(DEV_V3_SEEDS)
    confirm_v3 = set(CONFIRM_V3_RESERVED_SEEDS)
    if dev_v3 & USED_BEFORE_V3:
        raise ValueError("DEV_V3_SEEDS overlap an already-used seed")
    if confirm_v3 & USED_BEFORE_V3:
        raise ValueError("CONFIRM_V3_RESERVED_SEEDS overlap an already-used seed")
    if dev_v3 & confirm_v3:
        raise ValueError("V3 development and confirmation seeds overlap")


validate_seed_registry()
