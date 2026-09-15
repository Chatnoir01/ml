"""Held-out-blind checkpoint lifecycle orchestration for preregistered Phase 2G.

This module does not itself run the scientific experiment. It wires the frozen
four-checkpoint lifecycle through injected checkpoint-training and GA-block
callbacks so that arm semantics can be tested without real neural training or
held-out H access.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
import hashlib
import json
from typing import Any

from .cryptoshield import validate_sbox
from .phase2g import ARMS, CHECKPOINT_GENERATIONS, EVOLUTION_SEEDS
from .phase2g_curriculum import freeze_checkpoint_curriculum
from .phase2g_preconditions import make_s_shuffle_stream
from .provenance import fingerprint_sbox

SBox = tuple[int, ...]
CheckpointTrainer = Callable[..., Any]
EvolutionBlock = Callable[..., Sequence[Sequence[int]]]
POPULATION_SIZE = 20
EVOLUTION_GENERATIONS = 20


def _freeze_population(
    population: Sequence[Sequence[int]], *, role: str
) -> tuple[SBox, ...]:
    if len(population) != POPULATION_SIZE:
        raise ValueError(
            f"Phase-2G {role} population must contain exactly {POPULATION_SIZE} candidates"
        )
    frozen = tuple(validate_sbox(candidate) for candidate in population)
    if len(set(frozen)) != POPULATION_SIZE:
        raise ValueError(
            f"Phase-2G {role} population must contain {POPULATION_SIZE} unique candidates"
        )
    return frozen


def _population_fingerprints(population: Sequence[SBox]) -> tuple[str, ...]:
    return tuple(fingerprint_sbox(candidate) for candidate in population)


def _curriculum_digest(curriculum: Sequence[SBox]) -> str:
    material = "\n".join(_population_fingerprints(curriculum)).encode("ascii")
    return hashlib.sha256(material).hexdigest()


def _canonical(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def run_phase2g_checkpoint_lifecycle(
    *,
    arm: str,
    evolution_seed: int,
    initial_population: Sequence[Sequence[int]],
    train_checkpoint: CheckpointTrainer,
    evolve_block: EvolutionBlock,
) -> dict[str, Any]:
    """Execute the frozen four-checkpoint Phase-2G lifecycle with injected work.

    The runner enforces only preregistered orchestration semantics:

    - checkpoints are exactly 0, 5, 10 and 15;
    - each checkpoint governs the following five-generation block;
    - F always trains on the exact initial curriculum;
    - C/A/S train on the exact current population;
    - C checkpoint models are audit-only and cannot enable neural selection;
    - F/A enable candidate-specific neural selection inside downstream B1 logic;
    - S receives one fresh persistent shuffled-control stream per checkpoint;
    - no held-out H module, seed, scorer or result is imported or accessed here.

    ``train_checkpoint`` represents one complete checkpoint bundle. The later
    scientific adapter is responsible for expanding that bundle to the exact 16
    shared models and for receipting the exact training budget.
    """

    frozen_arm = str(arm)
    frozen_seed = int(evolution_seed)
    if frozen_arm not in ARMS:
        raise ValueError(f"unsupported Phase-2G arm {frozen_arm!r}")
    if frozen_seed not in EVOLUTION_SEEDS:
        raise ValueError(f"unregistered Phase-2G evolution seed {frozen_seed!r}")
    if not callable(train_checkpoint):
        raise TypeError("Phase-2G train_checkpoint must be callable")
    if not callable(evolve_block):
        raise TypeError("Phase-2G evolve_block must be callable")

    initial = _freeze_population(initial_population, role="initial")
    current = initial
    checkpoint_records: list[dict[str, Any]] = []

    for index, checkpoint_generation in enumerate(CHECKPOINT_GENERATIONS):
        start_generation = int(checkpoint_generation)
        end_generation = (
            int(CHECKPOINT_GENERATIONS[index + 1])
            if index + 1 < len(CHECKPOINT_GENERATIONS)
            else EVOLUTION_GENERATIONS
        )
        if end_generation - start_generation != 5:
            raise RuntimeError("Phase-2G checkpoint schedule drift")

        curriculum = freeze_checkpoint_curriculum(
            arm=frozen_arm,
            checkpoint_generation=start_generation,
            initial_population=initial,
            current_population=current,
        )
        model = train_checkpoint(
            arm=frozen_arm,
            evolution_seed=frozen_seed,
            checkpoint_generation=start_generation,
            curriculum=curriculum,
        )
        if model is None:
            raise RuntimeError("Phase-2G checkpoint trainer returned no model bundle")

        selection_enabled = frozen_arm != "C"
        shuffle_stream = (
            make_s_shuffle_stream(frozen_seed, start_generation)
            if frozen_arm == "S"
            else None
        )

        before = current
        evolved = evolve_block(
            population=before,
            start_generation=start_generation,
            end_generation=end_generation,
            selection_enabled=selection_enabled,
            model=model,
            shuffle_stream=shuffle_stream,
        )
        current = _freeze_population(
            evolved, role=f"post-block-{start_generation}-{end_generation}"
        )

        checkpoint_records.append(
            {
                "checkpoint_generation": start_generation,
                "block_start_generation": start_generation,
                "block_end_generation": end_generation,
                "selection_enabled": bool(selection_enabled),
                "curriculum_fingerprints": list(_population_fingerprints(curriculum)),
                "curriculum_digest_sha256": _curriculum_digest(curriculum),
                "population_before_fingerprints": list(_population_fingerprints(before)),
                "population_after_fingerprints": list(_population_fingerprints(current)),
                "shuffle_rng_seed": (
                    int(shuffle_stream.rng_seed) if shuffle_stream is not None else None
                ),
            }
        )

    if len(checkpoint_records) != len(CHECKPOINT_GENERATIONS):
        raise RuntimeError("Phase-2G checkpoint lifecycle count drift")

    payload: dict[str, Any] = {
        "schema_version": 1,
        "phase": "2G-lifecycle",
        "arm": frozen_arm,
        "seed": frozen_seed,
        "checkpoint_count": len(checkpoint_records),
        "generation_count": EVOLUTION_GENERATIONS,
        "initial_population_fingerprints": list(_population_fingerprints(initial)),
        "terminal_population_fingerprints": list(_population_fingerprints(current)),
        "checkpoints": checkpoint_records,
        "heldout_accessed": False,
    }
    payload["lifecycle_receipt_sha256"] = hashlib.sha256(_canonical(payload)).hexdigest()
    return payload
