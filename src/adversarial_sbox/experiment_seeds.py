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

DEV_V2_SEEDS = (307, 311, 313, 317, 331)
CONFIRM_V2_RESERVED_SEEDS = (401, 409, 419, 421, 431, 433, 439, 443, 449)

# Retain the original public name/semantics for historical tests and callers.
USED_BEFORE_V2 = (
    BASELINE_SEEDS
    | DEV_V1_SEEDS
    | CONFIRM_V1_SEEDS
    | STRICT_HISTORICAL_SEEDS
)

# Phase 1C: fresh-population DU-frontier development. Confirmation was never run.
DEV_PHASE1C_SEEDS = (503, 509, 521, 523, 541)
CONFIRM_PHASE1C_RESERVED_SEEDS = (601, 607, 613, 617, 619, 631, 641, 643, 647)

# Phase 1D: warm-start beam/swap continuation. Confirmation was never run.
DEV_PHASE1D_SEEDS = (701, 709, 719, 727, 733)
CONFIRM_PHASE1D_RESERVED_SEEDS = (809, 811, 821, 823, 827, 829, 839, 853, 857)

# Phase 1E: spectral/DDT-guided operator development. These are declared before
# any Phase-1E result exists. Confirmation seeds must remain untouched during dev.
DEV_PHASE1E_SEEDS = (907, 911, 919, 929, 937)
CONFIRM_PHASE1E_RESERVED_SEEDS = (1009, 1013, 1019, 1021, 1031, 1033, 1039, 1049, 1051)

USED_HISTORICAL = (
    USED_BEFORE_V2
    | set(DEV_V2_SEEDS)
    | set(CONFIRM_V2_RESERVED_SEEDS)
    | set(DEV_PHASE1C_SEEDS)
    | set(CONFIRM_PHASE1C_RESERVED_SEEDS)
    | set(DEV_PHASE1D_SEEDS)
    | set(CONFIRM_PHASE1D_RESERVED_SEEDS)
)


def validate_seed_registry() -> None:
    """Raise if development/confirmation isolation is violated."""

    dev_v2 = set(DEV_V2_SEEDS)
    confirm_v2 = set(CONFIRM_V2_RESERVED_SEEDS)
    if dev_v2 & USED_BEFORE_V2:
        raise ValueError("DEV_V2_SEEDS overlap an already-used seed")
    if confirm_v2 & USED_BEFORE_V2:
        raise ValueError("CONFIRM_V2_RESERVED_SEEDS overlap an already-used seed")

    pairs = (
        ("V2", dev_v2, confirm_v2),
        ("Phase1C", set(DEV_PHASE1C_SEEDS), set(CONFIRM_PHASE1C_RESERVED_SEEDS)),
        ("Phase1D", set(DEV_PHASE1D_SEEDS), set(CONFIRM_PHASE1D_RESERVED_SEEDS)),
        ("Phase1E", set(DEV_PHASE1E_SEEDS), set(CONFIRM_PHASE1E_RESERVED_SEEDS)),
    )
    for label, dev, confirm in pairs:
        if dev & confirm:
            raise ValueError(f"{label} development and confirmation seeds overlap")

    phase1e_dev = set(DEV_PHASE1E_SEEDS)
    phase1e_confirm = set(CONFIRM_PHASE1E_RESERVED_SEEDS)
    if phase1e_dev & USED_HISTORICAL:
        raise ValueError("DEV_PHASE1E_SEEDS overlap an already allocated seed")
    if phase1e_confirm & USED_HISTORICAL:
        raise ValueError("CONFIRM_PHASE1E_RESERVED_SEEDS overlap an already allocated seed")


validate_seed_registry()
