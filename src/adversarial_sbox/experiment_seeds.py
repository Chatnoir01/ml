"""Central seed registry for Phase-1 experiments.

A confirmatory or reserved seed is never reused by development. The registry also
documents one historical overlap discovered after two concurrent research branches
were merged. Later phases register their development and reserved confirmation
seeds before execution so accidental reuse becomes a test failure.
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

# Phase 1B / V2.
DEV_V2_SEEDS = (307, 311, 313, 317, 331)
CONFIRM_V2_RESERVED_SEEDS = (401, 409, 419, 421, 431, 433, 439, 443, 449)

# Phase 1C fresh-population DU-frontier experiment. Confirmation was not executed;
# the reserved seeds remain quarantined rather than being silently recycled.
PHASE1C_DEV_SEEDS = (503, 509, 521, 523, 541)
PHASE1C_CONFIRM_RESERVED_SEEDS = (601, 607, 613, 617, 619, 631, 641, 643, 647)

# Phase 1D verified warm-start continuation. Confirmation was not executed and the
# reserved seeds remain quarantined.
PHASE1D_DEV_SEEDS = (701, 709, 719, 727, 733)
PHASE1D_CONFIRM_RESERVED_SEEDS = (809, 811, 821, 823, 827, 829, 839, 853, 857)

# Phase 1E hotspot-guided operator development and completed confirmation.
PHASE1E_DEV_SEEDS = (907, 911, 919, 929, 937)
PHASE1E_CONFIRM_RESERVED_SEEDS = (1009, 1013, 1019, 1021, 1031, 1033, 1039, 1049, 1051)

# Phase 1F fresh-population bridge experiment. Declared before any Phase-1F run.
PHASE1F_DEV_SEEDS = (1103, 1109, 1117, 1123, 1129)
PHASE1F_CONFIRM_RESERVED_SEEDS = (1201, 1213, 1217, 1223, 1229, 1231, 1237, 1249, 1259)

# Phase 1G annealed-escape warm-start mechanism experiment. Declared before any
# Phase-1G development result. Confirmation seeds are quarantined unless the
# preregistered development prerequisite is met.
PHASE1G_DEV_SEEDS = (1301, 1303, 1307, 1319, 1321)
PHASE1G_CONFIRM_RESERVED_SEEDS = (1409, 1423, 1427, 1429, 1433, 1439, 1447, 1451, 1453)

# Phase 1H plateau-directed mutation experiment. Declared before implementation
# results or any Phase-1H development execution.
PHASE1H_DEV_SEEDS = (1501, 1511, 1523, 1531, 1543)
PHASE1H_CONFIRM_RESERVED_SEEDS = (1601, 1607, 1609, 1613, 1619, 1621, 1627, 1637, 1657)

# Phase 1I fresh-population transfer of the Phase-1H plateau-directed proposal
# selector. Declared before implementation results or any Phase-1I execution.
PHASE1I_DEV_SEEDS = (1709, 1721, 1723, 1733, 1741)
PHASE1I_CONFIRM_RESERVED_SEEDS = (1801, 1811, 1823, 1831, 1847, 1861, 1871, 1873, 1877)

# Phase 1L fresh-population ITO-aware Pareto development. Declared before any
# Phase-1L scientific execution. Reserved confirmation seeds remain quarantined
# unless the preregistered five-seed development gate passes.
PHASE1L_DEV_SEEDS = (1901, 1907, 1913, 1931, 1933)
PHASE1L_CONFIRM_RESERVED_SEEDS = (2003, 2011, 2017, 2027, 2029, 2039, 2053, 2063, 2069)

# Phase 1M DDT-first fresh-population repair experiment. Declared before
# implementation results or any Phase-1M scientific execution. Confirmation
# seeds remain quarantined unless every preregistered development prerequisite
# passes.
PHASE1M_DEV_SEEDS = (2111, 2113, 2129, 2131, 2137)
PHASE1M_CONFIRM_RESERVED_SEEDS = (2203, 2207, 2213, 2221, 2237, 2239, 2243, 2251, 2267)

USED_BEFORE_V2 = (
    BASELINE_SEEDS
    | DEV_V1_SEEDS
    | CONFIRM_V1_SEEDS
    | STRICT_HISTORICAL_SEEDS
)


def _as_set(values) -> set[int]:
    return set(values)


def validate_seed_registry() -> None:
    """Raise if any post-historical experiment reuses a seed unexpectedly."""

    blocks = [
        ("DEV_V2_SEEDS", _as_set(DEV_V2_SEEDS)),
        ("CONFIRM_V2_RESERVED_SEEDS", _as_set(CONFIRM_V2_RESERVED_SEEDS)),
        ("PHASE1C_DEV_SEEDS", _as_set(PHASE1C_DEV_SEEDS)),
        ("PHASE1C_CONFIRM_RESERVED_SEEDS", _as_set(PHASE1C_CONFIRM_RESERVED_SEEDS)),
        ("PHASE1D_DEV_SEEDS", _as_set(PHASE1D_DEV_SEEDS)),
        ("PHASE1D_CONFIRM_RESERVED_SEEDS", _as_set(PHASE1D_CONFIRM_RESERVED_SEEDS)),
        ("PHASE1E_DEV_SEEDS", _as_set(PHASE1E_DEV_SEEDS)),
        ("PHASE1E_CONFIRM_RESERVED_SEEDS", _as_set(PHASE1E_CONFIRM_RESERVED_SEEDS)),
        ("PHASE1F_DEV_SEEDS", _as_set(PHASE1F_DEV_SEEDS)),
        ("PHASE1F_CONFIRM_RESERVED_SEEDS", _as_set(PHASE1F_CONFIRM_RESERVED_SEEDS)),
        ("PHASE1G_DEV_SEEDS", _as_set(PHASE1G_DEV_SEEDS)),
        ("PHASE1G_CONFIRM_RESERVED_SEEDS", _as_set(PHASE1G_CONFIRM_RESERVED_SEEDS)),
        ("PHASE1H_DEV_SEEDS", _as_set(PHASE1H_DEV_SEEDS)),
        ("PHASE1H_CONFIRM_RESERVED_SEEDS", _as_set(PHASE1H_CONFIRM_RESERVED_SEEDS)),
        ("PHASE1I_DEV_SEEDS", _as_set(PHASE1I_DEV_SEEDS)),
        ("PHASE1I_CONFIRM_RESERVED_SEEDS", _as_set(PHASE1I_CONFIRM_RESERVED_SEEDS)),
        ("PHASE1L_DEV_SEEDS", _as_set(PHASE1L_DEV_SEEDS)),
        ("PHASE1L_CONFIRM_RESERVED_SEEDS", _as_set(PHASE1L_CONFIRM_RESERVED_SEEDS)),
        ("PHASE1M_DEV_SEEDS", _as_set(PHASE1M_DEV_SEEDS)),
        ("PHASE1M_CONFIRM_RESERVED_SEEDS", _as_set(PHASE1M_CONFIRM_RESERVED_SEEDS)),
    ]

    for name, values in blocks:
        if values & USED_BEFORE_V2:
            raise ValueError(f"{name} overlaps an already-used historical seed")

    for index, (left_name, left) in enumerate(blocks):
        for right_name, right in blocks[index + 1 :]:
            overlap = left & right
            if overlap:
                raise ValueError(
                    f"seed registry overlap between {left_name} and {right_name}: "
                    f"{sorted(overlap)}"
                )


validate_seed_registry()
