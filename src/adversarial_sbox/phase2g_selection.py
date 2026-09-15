"""Checkpoint score cache and protected B1 ordering for preregistered Phase 2G.

This module is intentionally held-out blind. It does not train models and it does
not run evolution. It validates inference-only score receipts, caches them at the
exact preregistered (arm, seed, checkpoint, fingerprint) scope, and delegates the
actual B1 geometry to the already-tested Phase-2F pure ordering contract.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
import hashlib
import json
import math
import random
from typing import Any

from .cryptoshield import validate_sbox
from .evolution import ClassicalMetrics, HardConstraints
from .phase2f import apply_phase2f_cutoff_order
from .phase2g import ARMS, CHECKPOINT_GENERATIONS, EVOLUTION_SEEDS
from .phase2g_shared_model import score_cache_key
from .provenance import fingerprint_sbox

SBox = tuple[int, ...]
ScorePayload = dict[str, Any]
CheckpointScorer = Callable[[Sequence[int]], ScorePayload]
ScoreCacheKey = tuple[str, int, int, str]


def _canonical_without_receipt(payload: ScorePayload) -> bytes:
    clean = {key: value for key, value in payload.items() if key != "scientific_payload_sha256"}
    return json.dumps(clean, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _valid_sha256(value: str) -> bool:
    frozen = str(value)
    if len(frozen) != 64:
        return False
    try:
        int(frozen, 16)
    except ValueError:
        return False
    return True


@dataclass(frozen=True, slots=True)
class CheckpointScoreReceipt:
    cache_key: ScoreCacheKey
    fingerprint: str
    neural_advantage: float
    payload_sha256: str
    training_count: int
    payload: ScorePayload


class CheckpointScoreLedger:
    """Inference-only Phase-2G score cache for one arm/seed/checkpoint.

    A cache miss may call the injected checkpoint scorer once. A cache hit can
    never recompute the candidate with another Q seed block because checkpoint
    identity is part of the key. The scorer itself remains responsible for the
    sixteen-model Q inference geometry; this ledger verifies its scientific
    receipt before accepting the score.
    """

    def __init__(
        self,
        *,
        arm: str,
        evolution_seed: int,
        checkpoint_generation: int,
        scorer: CheckpointScorer,
    ) -> None:
        frozen_arm = str(arm)
        frozen_seed = int(evolution_seed)
        frozen_checkpoint = int(checkpoint_generation)
        if frozen_arm not in ARMS:
            raise ValueError(f"unsupported Phase-2G arm {frozen_arm!r}")
        if frozen_seed not in EVOLUTION_SEEDS:
            raise ValueError(f"unregistered Phase-2G evolution seed {frozen_seed!r}")
        if frozen_checkpoint not in CHECKPOINT_GENERATIONS:
            raise ValueError(f"generation {frozen_checkpoint!r} is not a Phase-2G checkpoint")
        if not callable(scorer):
            raise TypeError("Phase-2G checkpoint scorer must be callable")

        self.arm = frozen_arm
        self.evolution_seed = frozen_seed
        self.checkpoint_generation = frozen_checkpoint
        self._scorer = scorer
        self._cache: dict[ScoreCacheKey, CheckpointScoreReceipt] = {}

    @property
    def receipts(self) -> tuple[CheckpointScoreReceipt, ...]:
        return tuple(self._cache.values())

    @property
    def cache_size(self) -> int:
        return len(self._cache)

    def score(self, candidate: Sequence[int]) -> float:
        frozen = validate_sbox(candidate)
        fingerprint = fingerprint_sbox(frozen)
        key = score_cache_key(
            arm=self.arm,
            evolution_seed=self.evolution_seed,
            checkpoint_generation=self.checkpoint_generation,
            candidate_fingerprint=fingerprint,
        )
        cached = self._cache.get(key)
        if cached is not None:
            return cached.neural_advantage

        raw = self._scorer(frozen)
        if not isinstance(raw, dict):
            raise RuntimeError("Phase-2G score receipt must be a mapping")
        payload = json.loads(json.dumps(raw, sort_keys=True))

        payload_fingerprint = str(
            payload.get("candidate_fingerprint", payload.get("fingerprint", ""))
        )
        if payload_fingerprint != fingerprint:
            raise RuntimeError("Phase-2G score receipt fingerprint mismatch")
        if int(payload.get("training_count", -1)) != 0:
            raise RuntimeError("Phase-2G candidate scoring must be inference-only")

        score = float(payload.get("neural_advantage", float("nan")))
        if not math.isfinite(score):
            raise RuntimeError("Phase-2G score receipt contains non-finite neural advantage")

        stored_sha = str(payload.get("scientific_payload_sha256", ""))
        expected_sha = hashlib.sha256(_canonical_without_receipt(payload)).hexdigest()
        if not _valid_sha256(stored_sha) or stored_sha.lower() != expected_sha:
            raise RuntimeError("Phase-2G score receipt integrity failure")

        receipt = CheckpointScoreReceipt(
            cache_key=key,
            fingerprint=fingerprint,
            neural_advantage=score,
            payload_sha256=stored_sha.lower(),
            training_count=0,
            payload=payload,
        )
        self._cache[key] = receipt
        return score


def apply_phase2g_cutoff_order(
    items: Sequence[tuple[Any, ClassicalMetrics, float]],
    *,
    constraints: HardConstraints,
    arm: str,
    cutoff_metrics: ClassicalMetrics,
    shuffle_rng: random.Random | None,
) -> list[tuple[Any, ClassicalMetrics, float]]:
    """Apply Phase-2G scores without changing the frozen Phase-2F B1 geometry.

    C remains historical classical order. F and A both use the exact B1 ordering
    rule; their only scientific difference is how the upstream shared model's
    curriculum was built. S uses the same B1 group with deterministic shuffled
    candidate/score association. Delegating to Phase 2F prevents a Phase-2G
    implementation from silently widening the band or crossing an outside-band
    candidate.
    """

    frozen_arm = str(arm)
    if frozen_arm not in ARMS:
        raise ValueError(f"unsupported Phase-2G arm {frozen_arm!r}")
    if frozen_arm == "S" and shuffle_rng is None:
        raise ValueError("Phase-2G S arm requires a persistent shuffled-score RNG")

    mapped_arm = {
        "C": "C",
        "F": "B1",
        "A": "B1",
        "S": "SB1",
    }[frozen_arm]
    return apply_phase2f_cutoff_order(
        items,
        constraints=constraints,
        arm=mapped_arm,
        cutoff_metrics=cutoff_metrics,
        shuffle_rng=shuffle_rng,
    )
