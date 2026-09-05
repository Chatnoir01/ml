"""Phase 2A fresh-panel Neural Oracle qualification contracts.

Scientific protocol: ``research/PHASE2A_PROTOCOL.md``.

This module deliberately contains no evolutionary feedback path.  Phase 2A may
qualify a neural scoring procedure for a later, separately preregistered Phase 2B,
but cannot inject a neural score into GA selection itself.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Mapping, Sequence

from .cryptoshield import is_bijective, validate_sbox

SBox = tuple[int, ...]

PANEL_SIZE = 6

ORACLE_ARCHITECTURE = "bit_relu_mlp"
ORACLE_ROUNDS = 4
ORACLE_DIFFERENCES = (0x00000001, 0x00000100)

CHALLENGER_ARCHITECTURE = "byte_tanh_mlp"
CHALLENGER_ROUNDS = 5
CHALLENGER_DIFFERENCES = (0x00010000, 0x01000000)

DATASET_SEEDS = (51001, 51007, 51011, 51031, 51047)
MODEL_SEEDS = (61001, 61007, 61027, 61031, 61043)

TRAININGS_PER_SIDE = PANEL_SIZE * 2 * len(DATASET_SEEDS)
TOTAL_TRAININGS = 2 * TRAININGS_PER_SIDE

REQUIRED_CHECKS = (
    "training_count_exact",
    "panel_revalidated",
    "oracle_heterogeneity",
    "challenger_heterogeneity",
    "oracle_range",
    "challenger_range",
    "rank_replication",
    "oracle_signal",
    "challenger_signal",
    "deterministic_receipts",
)


@dataclass(frozen=True, slots=True)
class CandidateRecord:
    """Classical-only Phase-2A panel candidate receipt."""

    source_seed: int
    fingerprint: str
    sbox: SBox
    differential_uniformity: int
    nonlinearity: int
    max_linear_correlation: int
    algebraic_degree: int
    sac_score: float

    def canonical_payload(self) -> dict[str, object]:
        return {
            "source_seed": int(self.source_seed),
            "fingerprint": str(self.fingerprint),
            "sbox": [int(value) for value in self.sbox],
            "differential_uniformity": int(self.differential_uniformity),
            "nonlinearity": int(self.nonlinearity),
            "max_linear_correlation": int(self.max_linear_correlation),
            "algebraic_degree": int(self.algebraic_degree),
            "sac_score": float(self.sac_score),
        }


def is_phase2a_eligible(candidate: CandidateRecord) -> bool:
    """Return whether a record satisfies the preregistered classical panel gate."""

    try:
        frozen = validate_sbox(candidate.sbox)
    except (TypeError, ValueError):
        return False

    return (
        is_bijective(frozen)
        and candidate.differential_uniformity == 8
        and candidate.nonlinearity == 100
        and candidate.max_linear_correlation == 56
        and candidate.algebraic_degree == 7
        and abs(float(candidate.sac_score) - 0.5) <= 0.05
        and len(candidate.fingerprint) == 64
    )


def select_fresh_panel(records: Sequence[CandidateRecord]) -> tuple[CandidateRecord, ...]:
    """Select the frozen six-candidate panel using classical information only.

    Selection order is exactly the preregistered rule:
    eligible candidates -> lexicographically smallest fingerprint per source seed ->
    lexicographically smallest six representatives globally.
    """

    eligible = [record for record in records if is_phase2a_eligible(record)]
    per_seed: dict[int, CandidateRecord] = {}
    for record in sorted(eligible, key=lambda item: (item.source_seed, item.fingerprint)):
        current = per_seed.get(record.source_seed)
        if current is None or record.fingerprint < current.fingerprint:
            per_seed[record.source_seed] = record

    if len(per_seed) < PANEL_SIZE:
        raise ValueError(
            "Phase 2A requires at least six eligible source seeds before neural training"
        )

    selected = sorted(per_seed.values(), key=lambda item: item.fingerprint)[:PANEL_SIZE]
    return tuple(selected)


def panel_digest(panel: Sequence[CandidateRecord]) -> str:
    """SHA-256 receipt for the ordered, committed classical panel."""

    if len(panel) != PANEL_SIZE:
        raise ValueError(f"Phase 2A panel must contain exactly {PANEL_SIZE} candidates")
    payload = [record.canonical_payload() for record in panel]
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def qualification_verdict(checks: Mapping[str, bool]) -> str:
    """Return the frozen Phase-2A verdict from the complete check set."""

    missing = [name for name in REQUIRED_CHECKS if name not in checks]
    if missing:
        raise ValueError(f"missing Phase 2A qualification checks: {', '.join(missing)}")
    passed = all(bool(checks[name]) for name in REQUIRED_CHECKS)
    return "phase2a_oracle_qualified" if passed else "phase2a_oracle_not_qualified"
