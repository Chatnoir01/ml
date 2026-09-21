"""Held-out-blind checkpoint-model adapter for preregistered Phase 2G.

This module expands one lifecycle checkpoint into the exact 16 shared models and
binds them to inference-only candidate scoring. It does not run GA evolution,
import held-out H validation, or authorize scientific execution.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
import hashlib
import json
from typing import Any

from .cryptoshield import validate_sbox
from .phase2g import (
    ARMS,
    CHECKPOINT_GENERATIONS,
    EVOLUTION_SEEDS,
    TRAINING_DATASET_BASE_SEEDS,
    TRAINING_MODEL_BASE_SEEDS,
    TRAININGS_PER_CHECKPOINT,
    expanded_checkpoint_seed_block,
)
from .phase2g_selection import CheckpointScoreLedger
from .phase2g_shared_model import (
    INPUT_DIFFERENCES,
    REPLICATES,
    score_candidate_checkpoint,
    train_shared_checkpoint_model,
)
from .provenance import fingerprint_sbox

SBox = tuple[int, ...]
ModelTrainer = Callable[..., Any]
CandidateScorer = Callable[..., dict[str, Any]]


def _validate_identity(
    *, arm: str, evolution_seed: int, checkpoint_generation: int
) -> tuple[str, int, int, int]:
    frozen_arm = str(arm)
    frozen_seed = int(evolution_seed)
    frozen_checkpoint = int(checkpoint_generation)
    if frozen_arm not in ARMS:
        raise ValueError(f"unsupported Phase-2G arm {frozen_arm!r}")
    if frozen_seed not in EVOLUTION_SEEDS:
        raise ValueError(f"unregistered Phase-2G evolution seed {frozen_seed!r}")
    if frozen_checkpoint not in CHECKPOINT_GENERATIONS:
        raise ValueError(
            f"generation {frozen_checkpoint!r} is not a preregistered Phase-2G checkpoint"
        )
    return (
        frozen_arm,
        frozen_seed,
        frozen_checkpoint,
        CHECKPOINT_GENERATIONS.index(frozen_checkpoint),
    )


def _canonical_curriculum(curriculum: Sequence[Sequence[int]]) -> tuple[SBox, ...]:
    if len(curriculum) != 20:
        raise ValueError("Phase-2G checkpoint curriculum must contain exactly 20 candidates")
    frozen = tuple(validate_sbox(candidate) for candidate in curriculum)
    if len(set(frozen)) != 20:
        raise ValueError("Phase-2G checkpoint curriculum must contain 20 unique candidates")
    return tuple(sorted(frozen, key=fingerprint_sbox))


def _curriculum_digest(curriculum: Sequence[SBox]) -> str:
    blob = "\n".join(fingerprint_sbox(candidate) for candidate in curriculum).encode("ascii")
    return hashlib.sha256(blob).hexdigest()


def _is_hex64(value: object) -> bool:
    text = str(value)
    if len(text) != 64:
        return False
    try:
        int(text, 16)
    except ValueError:
        return False
    return True


def _require_model_identity(
    model: Any,
    *,
    arm: str,
    evolution_seed: int,
    checkpoint_generation: int,
    difference: int,
    replicate: int,
    dataset_seed: int,
    model_seed: int,
    curriculum_digest_sha256: str,
) -> None:
    expected = {
        "arm": arm,
        "evolution_seed": evolution_seed,
        "checkpoint_generation": checkpoint_generation,
        "difference": difference,
        "replicate": replicate,
        "dataset_seed": dataset_seed,
        "model_seed": model_seed,
    }
    for field, value in expected.items():
        if not hasattr(model, field):
            raise RuntimeError(f"Phase-2G checkpoint model missing identity field {field!r}")
        actual = getattr(model, field)
        if field == "arm":
            matches = str(actual) == str(value)
        else:
            matches = int(actual) == int(value)
        if not matches:
            raise RuntimeError(f"Phase-2G checkpoint model identity drift for {field}")

    if str(getattr(model, "curriculum_digest_sha256", "")) != curriculum_digest_sha256:
        raise RuntimeError("Phase-2G checkpoint model curriculum digest drift")
    if not _is_hex64(getattr(model, "state_sha256", "")):
        raise RuntimeError("Phase-2G checkpoint model state receipt is invalid")


def _checkpoint_training_receipt(
    *,
    arm: str,
    evolution_seed: int,
    checkpoint_generation: int,
    curriculum_digest_sha256: str,
    models: Sequence[Any],
) -> str:
    rows = []
    for model in sorted(models, key=lambda value: (int(value.difference), int(value.replicate))):
        rows.append(
            {
                "difference": int(model.difference),
                "replicate": int(model.replicate),
                "dataset_seed": int(model.dataset_seed),
                "model_seed": int(model.model_seed),
                "curriculum_digest_sha256": str(model.curriculum_digest_sha256),
                "state_sha256": str(model.state_sha256),
            }
        )
    payload = {
        "schema_version": 1,
        "experiment": "phase2g_checkpoint_training",
        "arm": str(arm),
        "evolution_seed": int(evolution_seed),
        "checkpoint_generation": int(checkpoint_generation),
        "curriculum_digest_sha256": str(curriculum_digest_sha256),
        "model_count": len(rows),
        "training_count": len(rows),
        "models": rows,
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True, slots=True)
class Phase2GCheckpointBundle:
    """Exact frozen 16-model checkpoint bundle used by one five-generation block."""

    arm: str
    evolution_seed: int
    checkpoint_generation: int
    curriculum: tuple[SBox, ...]
    curriculum_digest_sha256: str
    models: tuple[Any, ...]
    training_count: int
    training_receipt_sha256: str

    @property
    def model_count(self) -> int:
        return len(self.models)


def build_phase2g_checkpoint_bundle(
    *,
    arm: str,
    evolution_seed: int,
    checkpoint_generation: int,
    curriculum: Sequence[Sequence[int]],
    train_model: ModelTrainer = train_shared_checkpoint_model,
) -> Phase2GCheckpointBundle:
    """Train the exact 2-difference × 8-replicate shared model grid for a checkpoint."""

    frozen_arm, frozen_seed, frozen_checkpoint, checkpoint_index = _validate_identity(
        arm=arm,
        evolution_seed=evolution_seed,
        checkpoint_generation=checkpoint_generation,
    )
    if not callable(train_model):
        raise TypeError("Phase-2G checkpoint model trainer must be callable")

    canonical = _canonical_curriculum(curriculum)
    curriculum_digest = _curriculum_digest(canonical)
    t_seeds = expanded_checkpoint_seed_block(
        TRAINING_DATASET_BASE_SEEDS, checkpoint_index
    )
    m_seeds = expanded_checkpoint_seed_block(
        TRAINING_MODEL_BASE_SEEDS, checkpoint_index
    )
    if len(t_seeds) != REPLICATES or len(m_seeds) != REPLICATES:
        raise RuntimeError("Phase-2G checkpoint T/M seed block geometry drift")

    models: list[Any] = []
    seen: set[tuple[int, int]] = set()
    for difference in INPUT_DIFFERENCES:
        for replicate in range(REPLICATES):
            dataset_seed = int(t_seeds[replicate])
            model_seed = int(m_seeds[replicate])
            model = train_model(
                arm=frozen_arm,
                evolution_seed=frozen_seed,
                checkpoint_generation=frozen_checkpoint,
                difference=int(difference),
                replicate=int(replicate),
                curriculum=canonical,
                dataset_seed=dataset_seed,
                model_seed=model_seed,
            )
            if model is None:
                raise RuntimeError("Phase-2G checkpoint trainer returned no model")
            _require_model_identity(
                model,
                arm=frozen_arm,
                evolution_seed=frozen_seed,
                checkpoint_generation=frozen_checkpoint,
                difference=int(difference),
                replicate=int(replicate),
                dataset_seed=dataset_seed,
                model_seed=model_seed,
                curriculum_digest_sha256=curriculum_digest,
            )
            key = (int(difference), int(replicate))
            if key in seen:
                raise RuntimeError("duplicate Phase-2G checkpoint model identity")
            seen.add(key)
            models.append(model)

    expected_grid = {
        (int(difference), int(replicate))
        for difference in INPUT_DIFFERENCES
        for replicate in range(REPLICATES)
    }
    if seen != expected_grid or len(models) != TRAININGS_PER_CHECKPOINT:
        raise RuntimeError("Phase-2G checkpoint model grid is incomplete")

    receipt = _checkpoint_training_receipt(
        arm=frozen_arm,
        evolution_seed=frozen_seed,
        checkpoint_generation=frozen_checkpoint,
        curriculum_digest_sha256=curriculum_digest,
        models=models,
    )
    return Phase2GCheckpointBundle(
        arm=frozen_arm,
        evolution_seed=frozen_seed,
        checkpoint_generation=frozen_checkpoint,
        curriculum=canonical,
        curriculum_digest_sha256=curriculum_digest,
        models=tuple(models),
        training_count=TRAININGS_PER_CHECKPOINT,
        training_receipt_sha256=receipt,
    )


def make_phase2g_checkpoint_score_ledger(
    bundle: Phase2GCheckpointBundle,
    *,
    score_candidate: CandidateScorer = score_candidate_checkpoint,
) -> CheckpointScoreLedger:
    """Bind an exact checkpoint bundle to the preregistered inference-only score cache."""

    if not isinstance(bundle, Phase2GCheckpointBundle):
        raise TypeError("Phase-2G score ledger requires a Phase2GCheckpointBundle")
    if bundle.model_count != TRAININGS_PER_CHECKPOINT or bundle.training_count != TRAININGS_PER_CHECKPOINT:
        raise RuntimeError("Phase-2G checkpoint bundle training/model count drift")
    if not _is_hex64(bundle.training_receipt_sha256):
        raise RuntimeError("Phase-2G checkpoint bundle training receipt is invalid")
    if not callable(score_candidate):
        raise TypeError("Phase-2G candidate scorer must be callable")

    def scorer(candidate: Sequence[int]) -> dict[str, Any]:
        payload = score_candidate(candidate, models=bundle.models)
        if not isinstance(payload, dict):
            raise RuntimeError("Phase-2G checkpoint candidate scorer must return a mapping")
        if str(payload.get("arm", "")) != bundle.arm:
            raise RuntimeError("Phase-2G checkpoint score arm drift")
        if int(payload.get("evolution_seed", -1)) != bundle.evolution_seed:
            raise RuntimeError("Phase-2G checkpoint score evolution-seed drift")
        if int(payload.get("checkpoint_generation", -1)) != bundle.checkpoint_generation:
            raise RuntimeError("Phase-2G checkpoint score checkpoint drift")
        if int(payload.get("model_count", -1)) != TRAININGS_PER_CHECKPOINT:
            raise RuntimeError("Phase-2G checkpoint score model-count drift")
        if int(payload.get("training_count", -1)) != 0:
            raise RuntimeError("Phase-2G checkpoint candidate scoring must be inference-only")
        return payload

    return CheckpointScoreLedger(
        arm=bundle.arm,
        evolution_seed=bundle.evolution_seed,
        checkpoint_generation=bundle.checkpoint_generation,
        scorer=scorer,
    )
