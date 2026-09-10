"""Pre-execution deterministic controls for preregistered Phase 2G.

This module contains no neural training, no evolution runner, and no held-out-H
access. It freezes the deterministic S shuffled-control stream clarified in
issue #118 before scientific execution, plus the exact 6-of-9 adaptation-activity
prerequisite classifier.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import random
from collections.abc import Sequence

from .phase2g import CHECKPOINT_GENERATIONS, EVOLUTION_SEEDS



def _validate_sha256(value: str, *, field: str) -> str:
    frozen = str(value).lower()
    if len(frozen) != 64:
        raise ValueError(f"{field} must be a 64-character SHA-256 hex digest")
    try:
        int(frozen, 16)
    except ValueError as exc:
        raise ValueError(f"{field} must be hexadecimal") from exc
    return frozen


def _validate_evolution_seed(seed: int) -> int:
    frozen = int(seed)
    if frozen not in EVOLUTION_SEEDS:
        raise ValueError(f"unregistered Phase-2G evolution seed {frozen!r}")
    return frozen


def _validate_checkpoint_generation(checkpoint_generation: int) -> int:
    frozen = int(checkpoint_generation)
    if frozen not in CHECKPOINT_GENERATIONS:
        raise ValueError(
            f"generation {frozen!r} is not a preregistered Phase-2G checkpoint"
        )
    return frozen


def s_shuffle_seed(evolution_seed: int, checkpoint_generation: int) -> int:
    """Derive the exact preregistered persistent S-stream integer seed.

    Seed material is ASCII ``phase2g:S:<evolution_seed>:<checkpoint_generation>``.
    The RNG seed is the unsigned big-endian integer represented by the first
    eight bytes of its SHA-256 digest.
    """

    seed = _validate_evolution_seed(evolution_seed)
    checkpoint = _validate_checkpoint_generation(checkpoint_generation)
    material = f"phase2g:S:{seed}:{checkpoint}".encode("ascii")
    digest = hashlib.sha256(material).digest()
    return int.from_bytes(digest[:8], byteorder="big", signed=False)


@dataclass(frozen=True, slots=True)
class SShuffleAssignmentReceipt:
    evolution_seed: int
    checkpoint_generation: int
    rng_seed: int
    draw_index: int
    before: tuple[tuple[str, float], ...]
    after: tuple[tuple[str, float], ...]
    receipt_sha256: str


class SShuffleStream:
    """One persistent shuffled-score stream for a single S arm/seed/checkpoint."""

    def __init__(self, evolution_seed: int, checkpoint_generation: int) -> None:
        self.evolution_seed = _validate_evolution_seed(evolution_seed)
        self.checkpoint_generation = _validate_checkpoint_generation(checkpoint_generation)
        self.rng_seed = s_shuffle_seed(self.evolution_seed, self.checkpoint_generation)
        self._rng = random.Random(self.rng_seed)
        self._draw_index = 0

    @property
    def draw_count(self) -> int:
        return self._draw_index

    @property
    def rng(self) -> random.Random:
        """Expose the persistent RNG object for the later selection runner only."""

        return self._rng

    def shuffle_assignment(
        self,
        candidate_fingerprints: Sequence[str],
        scores: Sequence[float],
    ) -> SShuffleAssignmentReceipt:
        fingerprints = tuple(str(value) for value in candidate_fingerprints)
        frozen_scores = tuple(float(value) for value in scores)
        if not fingerprints:
            raise ValueError("Phase-2G S shuffle requires a non-empty eligible B1 band")
        if len(fingerprints) != len(frozen_scores):
            raise ValueError("Phase-2G S shuffle fingerprint/score length mismatch")
        if len(set(fingerprints)) != len(fingerprints) or any(not value for value in fingerprints):
            raise ValueError("Phase-2G S shuffle requires unique non-empty fingerprints")
        if any(not math.isfinite(value) for value in frozen_scores):
            raise ValueError("Phase-2G S shuffle scores must be finite")

        before = tuple(zip(fingerprints, frozen_scores))
        shuffled_scores = list(frozen_scores)
        self._rng.shuffle(shuffled_scores)
        after = tuple(zip(fingerprints, tuple(shuffled_scores)))

        draw_index = self._draw_index
        payload = {
            "schema_version": 1,
            "arm": "S",
            "evolution_seed": self.evolution_seed,
            "checkpoint_generation": self.checkpoint_generation,
            "rng_seed": self.rng_seed,
            "draw_index": draw_index,
            "before": [[fp, score] for fp, score in before],
            "after": [[fp, score] for fp, score in after],
        }
        receipt_sha256 = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        self._draw_index += 1

        return SShuffleAssignmentReceipt(
            evolution_seed=self.evolution_seed,
            checkpoint_generation=self.checkpoint_generation,
            rng_seed=self.rng_seed,
            draw_index=draw_index,
            before=before,
            after=after,
            receipt_sha256=receipt_sha256,
        )


def make_s_shuffle_stream(
    evolution_seed: int, checkpoint_generation: int
) -> SShuffleStream:
    return SShuffleStream(evolution_seed, checkpoint_generation)


@dataclass(frozen=True, slots=True)
class AdaptationSeedEvidence:
    """Per-seed evidence for the two frozen adaptation-activity conditions.

    ``adaptive_checkpoint_curriculum_digests_sha256`` contains checkpoint 1/2/3
    (generations 5/10/15). Checkpoint 0 is intentionally omitted because it is
    the initial curriculum and cannot establish adaptation.
    """

    evolution_seed: int
    initial_curriculum_digest_sha256: str
    adaptive_checkpoint_curriculum_digests_sha256: tuple[str, str, str]
    different_a_vs_f_ordering_in_fully_eligible_b1: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "evolution_seed", _validate_evolution_seed(self.evolution_seed))
        object.__setattr__(
            self,
            "initial_curriculum_digest_sha256",
            _validate_sha256(
                self.initial_curriculum_digest_sha256,
                field="initial_curriculum_digest_sha256",
            ),
        )
        checkpoint_digests = tuple(self.adaptive_checkpoint_curriculum_digests_sha256)
        if len(checkpoint_digests) != 3:
            raise ValueError("Phase-2G adaptation evidence requires checkpoint 1/2/3 digests")
        object.__setattr__(
            self,
            "adaptive_checkpoint_curriculum_digests_sha256",
            tuple(
                _validate_sha256(value, field="adaptive_checkpoint_curriculum_digest_sha256")
                for value in checkpoint_digests
            ),
        )
        if not isinstance(self.different_a_vs_f_ordering_in_fully_eligible_b1, bool):
            raise TypeError("Phase-2G ordering-difference evidence must be boolean")


@dataclass(frozen=True, slots=True)
class AdaptationActivitySummary:
    curriculum_changed_seed_count: int
    score_ordering_changed_seed_count: int
    curriculum_condition_passes: bool
    score_ordering_condition_passes: bool
    passes: bool


def classify_adaptation_activity(
    evidence: Sequence[AdaptationSeedEvidence],
) -> AdaptationActivitySummary:
    """Apply the exact preregistered two-part >=6/9 adaptation prerequisite."""

    rows = tuple(evidence)
    if len(rows) != len(EVOLUTION_SEEDS):
        raise ValueError("Phase-2G adaptation activity requires exactly nine seed records")
    if any(not isinstance(row, AdaptationSeedEvidence) for row in rows):
        raise TypeError("Phase-2G adaptation activity requires AdaptationSeedEvidence rows")

    seeds = tuple(row.evolution_seed for row in rows)
    if len(set(seeds)) != len(EVOLUTION_SEEDS) or set(seeds) != set(EVOLUTION_SEEDS):
        raise ValueError("Phase-2G adaptation activity seed evidence must match the exact registry")

    curriculum_changed_seed_count = sum(
        any(
            digest != row.initial_curriculum_digest_sha256
            for digest in row.adaptive_checkpoint_curriculum_digests_sha256
        )
        for row in rows
    )
    score_ordering_changed_seed_count = sum(
        row.different_a_vs_f_ordering_in_fully_eligible_b1 for row in rows
    )

    curriculum_condition_passes = curriculum_changed_seed_count >= 6
    score_ordering_condition_passes = score_ordering_changed_seed_count >= 6
    return AdaptationActivitySummary(
        curriculum_changed_seed_count=int(curriculum_changed_seed_count),
        score_ordering_changed_seed_count=int(score_ordering_changed_seed_count),
        curriculum_condition_passes=bool(curriculum_condition_passes),
        score_ordering_condition_passes=bool(score_ordering_condition_passes),
        passes=bool(curriculum_condition_passes and score_ordering_condition_passes),
    )
