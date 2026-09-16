"""RED contract for the real Phase 2G checkpoint-model adapter.

Synthetic only: this test must not perform real neural training, GA evolution, or
held-out H validation. It locks the adapter that expands one lifecycle checkpoint
into the exact 16 shared models and exposes inference-only cached Q scoring.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

import pytest

from adversarial_sbox.phase2g import (
    EVOLUTION_SEEDS,
    INPUT_DIFFERENCES if False else CHECKPOINT_GENERATIONS,
    TRAINING_DATASET_BASE_SEEDS,
    TRAINING_MODEL_BASE_SEEDS,
    expanded_checkpoint_seed_block,
)
from adversarial_sbox.phase2g_checkpoint_adapter import (
    build_phase2g_checkpoint_bundle,
    make_phase2g_checkpoint_score_ledger,
)
from adversarial_sbox.phase2g_shared_model import INPUT_DIFFERENCES
from adversarial_sbox.provenance import fingerprint_sbox


def _sbox(offset: int) -> tuple[int, ...]:
    return tuple(list(range(offset, 256)) + list(range(offset)))


def _curriculum() -> tuple[tuple[int, ...], ...]:
    return tuple(_sbox(index) for index in range(20))


@dataclass(frozen=True)
class FakeModel:
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


def _fake_trainer_calls():
    calls: list[dict[str, object]] = []

    def trainer(**kwargs):
        calls.append(dict(kwargs))
        state_bytes = (
            f"{kwargs['arm']}:{kwargs['evolution_seed']}:{kwargs['checkpoint_generation']}:"
            f"{kwargs['difference']}:{kwargs['replicate']}"
        ).encode("ascii")
        curriculum_blob = "\n".join(
            fingerprint_sbox(candidate) for candidate in kwargs["curriculum"]
        ).encode("ascii")
        return FakeModel(
            arm=str(kwargs["arm"]),
            evolution_seed=int(kwargs["evolution_seed"]),
            checkpoint_generation=int(kwargs["checkpoint_generation"]),
            difference=int(kwargs["difference"]),
            replicate=int(kwargs["replicate"]),
            dataset_seed=int(kwargs["dataset_seed"]),
            model_seed=int(kwargs["model_seed"]),
            curriculum_digest_sha256=hashlib.sha256(curriculum_blob).hexdigest(),
            state_sha256=hashlib.sha256(state_bytes).hexdigest(),
            state_bytes=state_bytes,
        )

    return calls, trainer


def _with_receipt(payload: dict[str, object]) -> dict[str, object]:
    frozen = dict(payload)
    raw = json.dumps(frozen, sort_keys=True, separators=(",", ":")).encode("utf-8")
    frozen["scientific_payload_sha256"] = hashlib.sha256(raw).hexdigest()
    return frozen


def test_checkpoint_bundle_expands_exact_16_model_grid_and_exact_tm_seeds() -> None:
    calls, trainer = _fake_trainer_calls()
    seed = EVOLUTION_SEEDS[0]
    checkpoint_generation = CHECKPOINT_GENERATIONS[1]

    bundle = build_phase2g_checkpoint_bundle(
        arm="A",
        evolution_seed=seed,
        checkpoint_generation=checkpoint_generation,
        curriculum=_curriculum(),
        train_model=trainer,
    )

    assert bundle.arm == "A"
    assert bundle.evolution_seed == seed
    assert bundle.checkpoint_generation == checkpoint_generation
    assert bundle.model_count == 16
    assert bundle.training_count == 16
    assert len(bundle.models) == 16
    assert len(calls) == 16

    assert {(int(call["difference"]), int(call["replicate"])) for call in calls} == {
        (difference, replicate)
        for difference in INPUT_DIFFERENCES
        for replicate in range(8)
    }

    expected_t = expanded_checkpoint_seed_block(TRAINING_DATASET_BASE_SEEDS, 1)
    expected_m = expanded_checkpoint_seed_block(TRAINING_MODEL_BASE_SEEDS, 1)
    for call in calls:
        replicate = int(call["replicate"])
        assert int(call["dataset_seed"]) == expected_t[replicate]
        assert int(call["model_seed"]) == expected_m[replicate]
        assert tuple(call["curriculum"]) == bundle.curriculum


def test_checkpoint_score_ledger_uses_all_16_models_and_caches_candidate_once() -> None:
    _calls, trainer = _fake_trainer_calls()
    bundle = build_phase2g_checkpoint_bundle(
        arm="F",
        evolution_seed=EVOLUTION_SEEDS[1],
        checkpoint_generation=CHECKPOINT_GENERATIONS[2],
        curriculum=_curriculum(),
        train_model=trainer,
    )
    scorer_calls: list[tuple[tuple[int, ...], tuple[FakeModel, ...]]] = []

    def score_candidate(candidate, *, models):
        frozen_models = tuple(models)
        scorer_calls.append((tuple(candidate), frozen_models))
        return _with_receipt(
            {
                "schema_version": 1,
                "experiment": "phase2g_checkpoint_candidate_inference",
                "purpose": "fitness_inference",
                "arm": bundle.arm,
                "evolution_seed": bundle.evolution_seed,
                "checkpoint_generation": bundle.checkpoint_generation,
                "fingerprint": fingerprint_sbox(candidate),
                "model_count": 16,
                "pairs_per_model": 400,
                "training_count": 0,
                "neural_advantage": 0.125,
                "models": [],
            }
        )

    ledger = make_phase2g_checkpoint_score_ledger(bundle, score_candidate=score_candidate)
    candidate = _sbox(55)
    assert ledger.score(candidate) == pytest.approx(0.125)
    assert ledger.score(candidate) == pytest.approx(0.125)
    assert len(scorer_calls) == 1
    assert scorer_calls[0][1] == bundle.models
    assert len(scorer_calls[0][1]) == 16
    assert ledger.cache_size == 1
    assert ledger.receipts[0].training_count == 0


def test_checkpoint_adapter_fails_closed_on_invalid_identity() -> None:
    _calls, trainer = _fake_trainer_calls()
    with pytest.raises(ValueError):
        build_phase2g_checkpoint_bundle(
            arm="X",
            evolution_seed=EVOLUTION_SEEDS[0],
            checkpoint_generation=0,
            curriculum=_curriculum(),
            train_model=trainer,
        )
    with pytest.raises(ValueError):
        build_phase2g_checkpoint_bundle(
            arm="A",
            evolution_seed=-1,
            checkpoint_generation=0,
            curriculum=_curriculum(),
            train_model=trainer,
        )
    with pytest.raises(ValueError):
        build_phase2g_checkpoint_bundle(
            arm="A",
            evolution_seed=EVOLUTION_SEEDS[0],
            checkpoint_generation=7,
            curriculum=_curriculum(),
            train_model=trainer,
        )
