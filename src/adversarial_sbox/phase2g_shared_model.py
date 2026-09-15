"""Fail-closed shared checkpoint models for preregistered Phase 2G.

This module implements only the checkpoint-scoped neural primitive required by
Phase 2G: deterministic shared-mixture training and inference-only candidate
scoring. It imports no held-out-H code and cannot authorize scientific execution.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
import hashlib
import json
import math
from collections.abc import Sequence
from typing import Any

from .cryptoshield import is_bijective, validate_sbox
from .datasets import PairSample, generate_balanced_pairs, split_dataset
from .neural100 import BATCH_SIZE, WEIGHT_DECAY, _advantage, _auc_from_scores, _numpy
from .neural_heterogeneity import (
    BYTE_EPOCHS,
    BYTE_HIDDEN_1,
    BYTE_HIDDEN_2,
    BYTE_LEARNING_RATE,
    ROUND_KEYS,
    _adam_update,
    _samples_to_byte_arrays,
    _sigmoid,
)
from .phase2g import (
    ARMS,
    CHECKPOINT_GENERATIONS,
    EVOLUTION_SEEDS,
    SCORING_DATASET_BASE_SEEDS,
    TRAINING_DATASET_BASE_SEEDS,
    TRAINING_MODEL_BASE_SEEDS,
    expanded_checkpoint_seed_block,
)
from .provenance import fingerprint_sbox
from .spn import ToySPN

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
DEPTH = 4

ModelKey = tuple[str, int, int, int, int]
ScoreCacheKey = tuple[str, int, int, str]
SBox = tuple[int, ...]


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


def _checkpoint_index(generation: int) -> int:
    frozen = _validate_checkpoint_generation(generation)
    return CHECKPOINT_GENERATIONS.index(frozen)


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


def _canonical_curriculum(curriculum: Sequence[Sequence[int]]) -> tuple[SBox, ...]:
    if len(curriculum) != CURRICULUM_SIZE:
        raise ValueError("Phase-2G shared curriculum must contain exactly 20 candidates")
    frozen = tuple(validate_sbox(candidate) for candidate in curriculum)
    if any(not is_bijective(candidate) for candidate in frozen):
        raise ValueError("Phase-2G shared curriculum requires bijective 8x8 S-Boxes")
    if len(set(frozen)) != CURRICULUM_SIZE:
        raise ValueError("Phase-2G shared curriculum must contain 20 unique candidates")
    return tuple(sorted(frozen, key=fingerprint_sbox))


def _curriculum_digest(curriculum: Sequence[Sequence[int]]) -> str:
    canonical = _canonical_curriculum(curriculum)
    blob = "\n".join(fingerprint_sbox(candidate) for candidate in canonical).encode("ascii")
    return hashlib.sha256(blob).hexdigest()


@dataclass(frozen=True, slots=True)
class SharedModelState:
    """Immutable identity + serialized state for one trained checkpoint model."""

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
    fingerprint = str(candidate_fingerprint)
    if not fingerprint:
        raise ValueError("candidate_fingerprint must not be empty")
    return (
        _validate_arm(arm),
        _validate_evolution_seed(evolution_seed),
        _validate_checkpoint_generation(checkpoint_generation),
        fingerprint,
    )


def build_shared_training_splits(
    curriculum: Sequence[Sequence[int]],
    *,
    difference: int,
    dataset_seed: int,
) -> tuple[tuple[PairSample, ...], tuple[PairSample, ...], tuple[PairSample, ...]]:
    """Build the exact 20×400 shared-mixture dataset for one T seed/difference."""

    canonical = _canonical_curriculum(curriculum)
    difference = _validate_difference(difference)
    dataset_seed = int(dataset_seed)
    if dataset_seed <= 0:
        raise ValueError("Phase-2G training dataset seed must be positive")

    train: list[PairSample] = []
    validation: list[PairSample] = []
    test: list[PairSample] = []
    keys = ROUND_KEYS[: DEPTH + 1]

    for sbox in canonical:
        cipher = ToySPN(sbox, keys)
        if cipher.rounds != DEPTH:
            raise RuntimeError("Phase-2G ToySPN depth drift")
        samples = generate_balanced_pairs(
            cipher,
            pair_count=PAIRS_PER_CURRICULUM_SBOX,
            input_difference=difference,
            seed=dataset_seed,
        )
        one_train, one_validation, one_test = split_dataset(samples)
        sizes = (len(one_train), len(one_validation), len(one_test))
        expected = (
            TRAIN_PAIRS_PER_SBOX,
            VALIDATION_PAIRS_PER_SBOX,
            TEST_PAIRS_PER_SBOX,
        )
        if sizes != expected:
            raise RuntimeError(f"Phase-2G per-S-Box split drift: {sizes} != {expected}")
        train.extend(one_train)
        validation.extend(one_validation)
        test.extend(one_test)

    global_sizes = (len(train), len(validation), len(test))
    expected_global = (SHARED_TRAIN_SIZE, SHARED_VALIDATION_SIZE, SHARED_TEST_SIZE)
    if global_sizes != expected_global:
        raise RuntimeError(
            f"Phase-2G shared split drift: {global_sizes} != {expected_global}"
        )
    return tuple(train), tuple(validation), tuple(test)


def _encode_array(value: Any) -> dict[str, Any]:
    np = _numpy()
    array = np.asarray(value, dtype=np.float32)
    little = array.astype("<f4", copy=False)
    return {
        "shape": list(little.shape),
        "data_b64": base64.b64encode(little.tobytes(order="C")).decode("ascii"),
    }


def _decode_array(payload: dict[str, Any]):
    np = _numpy()
    shape = tuple(int(value) for value in payload["shape"])
    raw = base64.b64decode(str(payload["data_b64"]).encode("ascii"), validate=True)
    expected_bytes = math.prod(shape) * 4 if shape else 4
    if len(raw) != expected_bytes:
        raise ValueError("Phase-2G serialized model array byte-size mismatch")
    return np.frombuffer(raw, dtype="<f4").copy().reshape(shape)


def _serialize_model_state(*, w1: Any, b1: Any, w2: Any, b2: Any, w3: Any, b3: Any) -> bytes:
    payload = {
        "schema_version": 1,
        "architecture": "byte_tanh_mlp",
        "w1": _encode_array(w1),
        "b1": _encode_array(b1),
        "w2": _encode_array(w2),
        "b2": _encode_array(b2),
        "w3": _encode_array(w3),
        "b3": _encode_array(b3),
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _deserialize_model_state(state_bytes: bytes):
    try:
        payload = json.loads(state_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("invalid Phase-2G serialized model state") from exc
    if payload.get("schema_version") != 1 or payload.get("architecture") != "byte_tanh_mlp":
        raise ValueError("Phase-2G serialized model identity drift")
    arrays = tuple(_decode_array(payload[name]) for name in ("w1", "b1", "w2", "b2", "w3", "b3"))
    w1, b1, w2, b2, w3, b3 = arrays
    expected_shapes = (
        (12, BYTE_HIDDEN_1),
        (BYTE_HIDDEN_1,),
        (BYTE_HIDDEN_1, BYTE_HIDDEN_2),
        (BYTE_HIDDEN_2,),
        (BYTE_HIDDEN_2,),
        (),
    )
    actual_shapes = tuple(tuple(value.shape) for value in arrays)
    if actual_shapes != expected_shapes:
        raise ValueError(
            f"Phase-2G serialized model shape drift: {actual_shapes} != {expected_shapes}"
        )
    return w1, b1, w2, b2, w3, b3


def _fit_shared_model_state_bytes(
    *,
    train_samples: Sequence[PairSample],
    validation_samples: Sequence[PairSample],
    test_samples: Sequence[PairSample],
    model_seed: int,
) -> bytes:
    """Train one fresh byte_tanh_mlp and return deterministic serialized weights."""

    if (len(train_samples), len(validation_samples), len(test_samples)) != (
        SHARED_TRAIN_SIZE,
        SHARED_VALIDATION_SIZE,
        SHARED_TEST_SIZE,
    ):
        raise ValueError("Phase-2G shared trainer received wrong split geometry")

    np = _numpy()
    x_train, y_train = _samples_to_byte_arrays(train_samples)
    # Materialize validation/test features now so malformed inputs fail before training.
    _samples_to_byte_arrays(validation_samples)
    _samples_to_byte_arrays(test_samples)

    rng = np.random.default_rng(int(model_seed))
    w1 = rng.normal(0.0, math.sqrt(1.0 / 12.0), size=(12, BYTE_HIDDEN_1)).astype(np.float32)
    b1 = np.zeros(BYTE_HIDDEN_1, dtype=np.float32)
    w2 = rng.normal(
        0.0,
        math.sqrt(1.0 / BYTE_HIDDEN_1),
        size=(BYTE_HIDDEN_1, BYTE_HIDDEN_2),
    ).astype(np.float32)
    b2 = np.zeros(BYTE_HIDDEN_2, dtype=np.float32)
    w3 = rng.normal(
        0.0,
        math.sqrt(1.0 / BYTE_HIDDEN_2),
        size=(BYTE_HIDDEN_2,),
    ).astype(np.float32)
    b3 = np.float32(0.0)

    m_w1 = np.zeros_like(w1)
    v_w1 = np.zeros_like(w1)
    m_b1 = np.zeros_like(b1)
    v_b1 = np.zeros_like(b1)
    m_w2 = np.zeros_like(w2)
    v_w2 = np.zeros_like(w2)
    m_b2 = np.zeros_like(b2)
    v_b2 = np.zeros_like(b2)
    m_w3 = np.zeros_like(w3)
    v_w3 = np.zeros_like(w3)
    m_b3 = np.float32(0.0)
    v_b3 = np.float32(0.0)
    step = 0

    for _epoch in range(BYTE_EPOCHS):
        order = rng.permutation(len(x_train))
        for start in range(0, len(order), BATCH_SIZE):
            batch_index = order[start : start + BATCH_SIZE]
            xb = x_train[batch_index]
            yb = y_train[batch_index]

            h1 = np.tanh(xb @ w1 + b1)
            h2 = np.tanh(h1 @ w2 + b2)
            logits = h2 @ w3 + b3
            probabilities = _sigmoid(logits)

            batch_size = float(len(batch_index))
            dlogits = (probabilities - yb) / batch_size
            grad_w3 = h2.T @ dlogits + WEIGHT_DECAY * w3
            grad_b3 = np.sum(dlogits, dtype=np.float32)
            dh2 = dlogits[:, None] * w3[None, :]
            dh2_pre = dh2 * (1.0 - h2 * h2)
            grad_w2 = h1.T @ dh2_pre + WEIGHT_DECAY * w2
            grad_b2 = np.sum(dh2_pre, axis=0, dtype=np.float32)
            dh1 = dh2_pre @ w2.T
            dh1_pre = dh1 * (1.0 - h1 * h1)
            grad_w1 = xb.T @ dh1_pre + WEIGHT_DECAY * w1
            grad_b1 = np.sum(dh1_pre, axis=0, dtype=np.float32)

            step += 1
            w1, m_w1, v_w1 = _adam_update(w1, m_w1, v_w1, grad_w1, step, BYTE_LEARNING_RATE)
            b1, m_b1, v_b1 = _adam_update(b1, m_b1, v_b1, grad_b1, step, BYTE_LEARNING_RATE)
            w2, m_w2, v_w2 = _adam_update(w2, m_w2, v_w2, grad_w2, step, BYTE_LEARNING_RATE)
            b2, m_b2, v_b2 = _adam_update(b2, m_b2, v_b2, grad_b2, step, BYTE_LEARNING_RATE)
            w3, m_w3, v_w3 = _adam_update(w3, m_w3, v_w3, grad_w3, step, BYTE_LEARNING_RATE)
            b3, m_b3, v_b3 = _adam_update(b3, m_b3, v_b3, grad_b3, step, BYTE_LEARNING_RATE)

    return _serialize_model_state(w1=w1, b1=b1, w2=w2, b2=b2, w3=w3, b3=b3)


def train_shared_checkpoint_model(
    *,
    arm: str,
    evolution_seed: int,
    checkpoint_generation: int,
    difference: int,
    replicate: int,
    curriculum: Sequence[Sequence[int]],
    dataset_seed: int,
    model_seed: int,
) -> SharedModelState:
    """Train exactly one fresh shared model for one preregistered checkpoint cell."""

    arm, evolution_seed, checkpoint_generation, difference, replicate = checkpoint_model_key(
        arm=arm,
        evolution_seed=evolution_seed,
        checkpoint_generation=checkpoint_generation,
        difference=difference,
        replicate=replicate,
    )
    checkpoint = _checkpoint_index(checkpoint_generation)
    expected_dataset_seed = expanded_checkpoint_seed_block(
        TRAINING_DATASET_BASE_SEEDS, checkpoint
    )[replicate]
    expected_model_seed = expanded_checkpoint_seed_block(
        TRAINING_MODEL_BASE_SEEDS, checkpoint
    )[replicate]
    if int(dataset_seed) != expected_dataset_seed:
        raise ValueError("Phase-2G checkpoint T-seed drift")
    if int(model_seed) != expected_model_seed:
        raise ValueError("Phase-2G checkpoint M-seed drift")

    canonical = _canonical_curriculum(curriculum)
    train, validation, test = build_shared_training_splits(
        canonical,
        difference=difference,
        dataset_seed=expected_dataset_seed,
    )
    state_bytes = _fit_shared_model_state_bytes(
        train_samples=train,
        validation_samples=validation,
        test_samples=test,
        model_seed=expected_model_seed,
    )
    return SharedModelState(
        arm=arm,
        evolution_seed=evolution_seed,
        checkpoint_generation=checkpoint_generation,
        difference=difference,
        replicate=replicate,
        dataset_seed=expected_dataset_seed,
        model_seed=expected_model_seed,
        curriculum_digest_sha256=_curriculum_digest(canonical),
        state_sha256=hashlib.sha256(state_bytes).hexdigest(),
        state_bytes=state_bytes,
    )


def _predict_probabilities(state: SharedModelState, samples: Sequence[PairSample]) -> list[float]:
    if hashlib.sha256(state.state_bytes).hexdigest() != state.state_sha256:
        raise RuntimeError("Phase-2G shared model state digest mismatch")
    np = _numpy()
    x, _labels = _samples_to_byte_arrays(samples)
    w1, b1, w2, b2, w3, b3 = _deserialize_model_state(state.state_bytes)
    scores = _sigmoid(np.tanh(np.tanh(x @ w1 + b1) @ w2 + b2) @ w3 + b3)
    return [float(value) for value in scores.tolist()]


def _canonical_without_receipt(payload: dict[str, Any]) -> bytes:
    stripped = {key: value for key, value in payload.items() if key != "scientific_payload_sha256"}
    return json.dumps(stripped, sort_keys=True, separators=(",", ":")).encode("utf-8")


def score_candidate_checkpoint(
    candidate: Sequence[int],
    *,
    models: Sequence[SharedModelState],
) -> dict[str, Any]:
    """Score one candidate by inference only across the exact 16 checkpoint models."""

    frozen = validate_sbox(candidate)
    if not is_bijective(frozen):
        raise ValueError("Phase-2G candidate scoring requires a bijective 8x8 S-Box")
    if len(models) != len(INPUT_DIFFERENCES) * REPLICATES:
        raise ValueError("Phase-2G candidate scoring requires exactly 16 shared models")

    identities = {(m.arm, m.evolution_seed, m.checkpoint_generation) for m in models}
    if len(identities) != 1:
        raise ValueError("Phase-2G candidate scoring models must share arm/seed/checkpoint")
    arm, evolution_seed, checkpoint_generation = next(iter(identities))
    _validate_arm(arm)
    _validate_evolution_seed(evolution_seed)
    checkpoint = _checkpoint_index(checkpoint_generation)

    expected_combinations = {
        (difference, replicate)
        for difference in INPUT_DIFFERENCES
        for replicate in range(REPLICATES)
    }
    indexed: dict[tuple[int, int], SharedModelState] = {}
    for model in models:
        key = (_validate_difference(model.difference), _validate_replicate(model.replicate))
        if key in indexed:
            raise ValueError("duplicate Phase-2G shared model identity")
        indexed[key] = model
    if set(indexed) != expected_combinations:
        raise ValueError("Phase-2G shared model grid is incomplete")

    q_seeds = expanded_checkpoint_seed_block(SCORING_DATASET_BASE_SEEDS, checkpoint)
    keys = ROUND_KEYS[: DEPTH + 1]
    per_model: list[dict[str, Any]] = []
    advantages: list[float] = []

    for difference in INPUT_DIFFERENCES:
        cipher = ToySPN(frozen, keys)
        if cipher.rounds != DEPTH:
            raise RuntimeError("Phase-2G ToySPN depth drift during inference")
        for replicate in range(REPLICATES):
            model = indexed[(difference, replicate)]
            q_seed = int(q_seeds[replicate])
            samples = generate_balanced_pairs(
                cipher,
                pair_count=SCORING_PAIRS_PER_MODEL_CANDIDATE,
                input_difference=difference,
                seed=q_seed,
            )
            labels = [int(sample.label) for sample in samples]
            probabilities = _predict_probabilities(model, samples)
            if len(probabilities) != len(labels):
                raise RuntimeError("Phase-2G inference score-length mismatch")
            auc = float(_auc_from_scores(labels, probabilities))
            advantage = float(_advantage(auc))
            if not math.isfinite(advantage):
                raise RuntimeError("Phase-2G inference returned non-finite neural advantage")
            advantages.append(advantage)
            per_model.append(
                {
                    "difference": int(difference),
                    "replicate": int(replicate),
                    "scoring_dataset_seed": q_seed,
                    "state_sha256": model.state_sha256,
                    "auc": auc,
                    "neural_advantage": advantage,
                }
            )

    mean_advantage = float(sum(advantages) / len(advantages))
    payload: dict[str, Any] = {
        "schema_version": 1,
        "experiment": "phase2g_checkpoint_candidate_inference",
        "purpose": "fitness_inference",
        "arm": arm,
        "evolution_seed": int(evolution_seed),
        "checkpoint_generation": int(checkpoint_generation),
        "fingerprint": fingerprint_sbox(frozen),
        "model_count": len(models),
        "pairs_per_model": SCORING_PAIRS_PER_MODEL_CANDIDATE,
        "training_count": 0,
        "neural_advantage": mean_advantage,
        "models": per_model,
    }
    payload["scientific_payload_sha256"] = hashlib.sha256(
        _canonical_without_receipt(payload)
    ).hexdigest()
    return payload
