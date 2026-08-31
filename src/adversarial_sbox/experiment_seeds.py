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

# Fresh V2 development seeds. These are development-only once this file lands.
DEV_V2_SEEDS = (307, 311, 313, 317, 331)

# Reserved now, before V2 development results exist. Development code must not
# consume them. They may be used only by a future frozen V2 confirmation.
CONFIRM_V2_RESERVED_SEEDS = (401, 409, 419, 421, 431, 433, 439, 443, 449)

USED_BEFORE_V2 = (
    BASELINE_SEEDS
    | DEV_V1_SEEDS
    | CONFIRM_V1_SEEDS
    | STRICT_HISTORICAL_SEEDS
)


def validate_seed_registry() -> None:
    """Raise if V2 development/confirmation isolation is violated."""

    dev_v2 = set(DEV_V2_SEEDS)
    confirm_v2 = set(CONFIRM_V2_RESERVED_SEEDS)
    if dev_v2 & USED_BEFORE_V2:
        raise ValueError("DEV_V2_SEEDS overlap an already-used seed")
    if confirm_v2 & USED_BEFORE_V2:
        raise ValueError("CONFIRM_V2_RESERVED_SEEDS overlap an already-used seed")
    if dev_v2 & confirm_v2:
        raise ValueError("V2 development and confirmation seeds overlap")


validate_seed_registry()
