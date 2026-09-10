"""Fail-closed identity contract for Phase 2G shared checkpoint models.

This module deliberately performs no neural training or inference.  It freezes the
preregistered shared-mixture geometry, immutable checkpoint model identity, and
cache-key scope that later RED->GREEN steps must consume without changing the
scientific protocol.
"""

from __future__ import annotations

from dataclasses import dataclass

from .phase2g import ARMS, CHECKPOINT_GENERATIONS, EVOLUTION_SEEDS

CURRICULUM_SIZE = 20
PAIRS_PER_CURRICULUM_SBOX = 400
TRAIN_PAIRS_PER_SBOX = 280
VALIDATION_PAIRS_PER_SBOX = 60
TEST_PAIRS_PER_SBOX = 60

SHARED_TRAIN_SIZE = CURRICULUM_SIZE * TRAIN_PAIRS_PER_SBOX
SHARED_VALIDATION_SIZE = CURRICULUM_SIZE * VALIDATION_PAIRS_PER_SBOX
SHARED_TEST_SIZE = CURRICULUM_SIZE * TEST_PAIRS_PER_SBOX

SCORING_PAIRS_PER_MODEL_CANDIDATE = 400
INPUT_DIFFERENCES = (0x00000001, 0x00000100)
REPLICATES = 8

ModelKey = tuple[str, int, int, int, int]
ScoreCacheKey = tuple[str, int, int, str]


def _validate_arm(arm: str) -> str:
    frozen = str(arm)
    if frozen not in ARMS:
        raise ValueError(f"unsupported Phase-2G arm {frozen!r}")
    return frozen


def _validate_evolution_seed(seed: int) -> int:
    frozen = int(seed)
    if frozen not in EVOLUTION_SEEDS:
        raise ValueError(f"unregistered Phase-2G evolution seed {frozen!r}")
    return frozen


def _validate_checkpoint_generation(generation: int) -> int:
    frozen = int(generation)
    if frozen not in CHECKPOINT_GENERATIONS:
        raise ValueError(f"generation {frozen!r} is not a Phase-2G checkpoint")
    return frozen


def _validate_difference(difference: int) -> int:
    frozen = int(difference)
    if frozen not in INPUT_DIFFERENCES:
        raise ValueError(f"unsupported Phase-2G input difference {frozen:#x}")
    return frozen


def _validate_replicate(replicate: int) -> int:
    frozen = int(replicate)
    if frozen not in range(REPLICATES):
        raise ValueError(f"Phase-2G replicate must be in [0, {REPLICATES - 1}]")
    return frozen


def _validate_sha256(value: str, *, field: str) -> str:
    frozen = str(value)
    if len(frozen) != 64:
        raise ValueError(f"{field} must be a 64-character SHA-256 hex digest")
    try:
        int(frozen, 16)
    except ValueError as exc:
        raise ValueError(f"{field} must be hexadecimal") from exc
    return frozen.lower()


@dataclass(frozen=True, slots=True)
class SharedModelState:
    """Immutable identity + serialized state for one trained checkpoint model.

    The byte payload is intentionally opaque here.  A later trainer step is
    responsible for producing it and proving that ``state_sha256`` matches the
    canonical serialization.  Keeping the contract immutable prevents accidental
    warm-start mutation or cross-checkpoint state leakage.
    """

    arm: str
    evolution_seed: int
    checkpoint_generation: int
    difference: int
    replicate: int
    dataset_seed: int
    model_seed: int
    curriculum_digest_sha256: str
    state_sha256: str
    state_bytes: bytes

    def __post_init__(self) -> None:
        object.__setattr__(self, "arm", _validate_arm(self.arm))
        object.__setattr__(self, "evolution_seed", _validate_evolution_seed(self.evolution_seed))
        object.__setattr__(
            self,
            "checkpoint_generation",
            _validate_checkpoint_generation(self.checkpoint_generation),
        )
        object.__setattr__(self, "difference", _validate_difference(self.difference))
        object.__setattr__(self, "replicate", _validate_replicate(self.replicate))
        object.__setattr__(self, "dataset_seed", int(self.dataset_seed))
        object.__setattr__(self, "model_seed", int(self.model_seed))
        if self.dataset_seed <= 0 or self.model_seed <= 0:
            raise ValueError("Phase-2G model seeds must be positive integers")
        object.__setattr__(
            self,
            "curriculum_digest_sha256",
            _validate_sha256(self.curriculum_digest_sha256, field="curriculum_digest_sha256"),
        )
        object.__setattr__(
            self,
            "state_sha256",
            _validate_sha256(self.state_sha256, field="state_sha256"),
        )
        if not isinstance(self.state_bytes, bytes) or not self.state_bytes:
            raise ValueError("state_bytes must be a non-empty immutable bytes payload")


def checkpoint_model_key(
    *,
    arm: str,
    evolution_seed: int,
    checkpoint_generation: int,
    difference: int,
    replicate: int,
) -> ModelKey:
    """Return the exact checkpoint-scoped key for one shared trained model."""

    return (
        _validate_arm(arm),
        _validate_evolution_seed(evolution_seed),
        _validate_checkpoint_generation(checkpoint_generation),
        _validate_difference(difference),
        _validate_replicate(replicate),
    )


def score_cache_key(
    *,
    arm: str,
    evolution_seed: int,
    checkpoint_generation: int,
    candidate_fingerprint: str,
) -> ScoreCacheKey:
    """Return the frozen candidate-score cache key required by preregistration."""

    fingerprint = str(candidate_fingerprint)
    if not fingerprint:
        raise ValueError("candidate_fingerprint must not be empty")
    return (
        _validate_arm(arm),
        _validate_evolution_seed(evolution_seed),
        _validate_checkpoint_generation(checkpoint_generation),
        fingerprint,
    )
