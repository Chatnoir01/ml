"""Held-out-blind complete arm/seed runner for preregistered Phase 2G.

This module composes the frozen four-checkpoint lifecycle into one complete
20-generation arm/seed cell while enforcing the exact classical and checkpoint
training budgets. It does not import or access held-out H and never performs a
terminal neural rerank.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
import hashlib
import json
from typing import Any

from .cryptoshield import validate_sbox
from .phase2g import (
    ARMS,
    CHECKPOINT_GENERATIONS,
    CHECKPOINT_TRAININGS_PER_CELL,
    EVOLUTION_SEEDS,
    TRAININGS_PER_CHECKPOINT,
)
from .phase2g_curriculum import freeze_checkpoint_curriculum
from .phase2g_preconditions import make_s_shuffle_stream
from .provenance import fingerprint_sbox

SBox = tuple[int, ...]
CheckpointTrainer = Callable[..., Any]
EvolutionBlock = Callable[..., Mapping[str, Any]]
TerminalSelector = Callable[[Sequence[SBox]], Sequence[int]]

POPULATION_SIZE = 20
EVOLUTION_GENERATIONS = 20
PROPOSALS_PER_GENERATION = 16
GENERATIONS_PER_CHECKPOINT = 5
CLASSICAL_INITIAL_EVALUATIONS = POPULATION_SIZE
CLASSICAL_EVALUATIONS_PER_BLOCK = GENERATIONS_PER_CHECKPOINT * PROPOSALS_PER_GENERATION
CLASSICAL_EVALUATIONS_PER_CELL = (
    CLASSICAL_INITIAL_EVALUATIONS
    + len(CHECKPOINT_GENERATIONS) * CLASSICAL_EVALUATIONS_PER_BLOCK
)


def _freeze_population(population: Sequence[Sequence[int]], *, role: str) -> tuple[SBox, ...]:
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


def _population_digest(population: Sequence[SBox]) -> str:
    material = "\n".join(_population_fingerprints(population)).encode("ascii")
    return hashlib.sha256(material).hexdigest()


def _canonical(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _training_count(bundle: Any) -> int:
    if not hasattr(bundle, "training_count"):
        raise RuntimeError("Phase-2G checkpoint bundle missing training_count")
    value = int(getattr(bundle, "training_count"))
    if value != TRAININGS_PER_CHECKPOINT:
        raise RuntimeError("Phase-2G checkpoint training-count drift")
    return value


def run_phase2g_arm(
    *,
    arm: str,
    evolution_seed: int,
    initial_population: Sequence[Sequence[int]],
    train_checkpoint: CheckpointTrainer,
    evolve_block: EvolutionBlock,
    select_terminal_classical_only: TerminalSelector,
) -> dict[str, Any]:
    """Run one complete preregistered Phase-2G arm/seed cell, held-out blind.

    Work is supplied through injected checkpoint-training and five-generation GA
    block callbacks so CI can exercise the orchestration without performing the
    scientific neural experiment. The callback contract is fail-closed:

    - exactly four checkpoints at generations 0/5/10/15;
    - exactly 16 checkpoint trainings at each checkpoint;
    - each block reports exactly five generations and 80 new classical evals;
    - the full cell therefore has exactly 340 unique classical evaluations;
    - C keeps neural selection disabled while still training audit models;
    - F uses the exact initial curriculum at every checkpoint;
    - A/S use their exact current population;
    - S receives one persistent preregistered shuffle stream per checkpoint;
    - terminal selection is delegated once to the historical classical-only rule;
    - held-out H is never imported or accessed here.
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
    if not callable(select_terminal_classical_only):
        raise TypeError("Phase-2G terminal selector must be callable")

    initial = _freeze_population(initial_population, role="initial")
    current = initial
    classical_evaluations = CLASSICAL_INITIAL_EVALUATIONS
    checkpoint_training_count = 0
    checkpoint_records: list[dict[str, Any]] = []
    selection_events: list[Any] = []

    for index, checkpoint_generation in enumerate(CHECKPOINT_GENERATIONS):
        start_generation = int(checkpoint_generation)
        end_generation = (
            int(CHECKPOINT_GENERATIONS[index + 1])
            if index + 1 < len(CHECKPOINT_GENERATIONS)
            else EVOLUTION_GENERATIONS
        )
        if end_generation - start_generation != GENERATIONS_PER_CHECKPOINT:
            raise RuntimeError("Phase-2G checkpoint schedule drift")

        curriculum = freeze_checkpoint_curriculum(
            arm=frozen_arm,
            checkpoint_generation=start_generation,
            initial_population=initial,
            current_population=current,
        )
        bundle = train_checkpoint(
            arm=frozen_arm,
            evolution_seed=frozen_seed,
            checkpoint_generation=start_generation,
            curriculum=curriculum,
        )
        if bundle is None:
            raise RuntimeError("Phase-2G checkpoint trainer returned no bundle")
        bundle_trainings = _training_count(bundle)
        checkpoint_training_count += bundle_trainings

        selection_enabled = frozen_arm != "C"
        shuffle_stream = (
            make_s_shuffle_stream(frozen_seed, start_generation)
            if frozen_arm == "S"
            else None
        )

        before = current
        block = evolve_block(
            population=before,
            start_generation=start_generation,
            end_generation=end_generation,
            selection_enabled=selection_enabled,
            model=bundle,
            shuffle_stream=shuffle_stream,
        )
        if not isinstance(block, Mapping):
            raise RuntimeError("Phase-2G evolution block must return a mapping receipt")
        if int(block.get("generation_count", -1)) != GENERATIONS_PER_CHECKPOINT:
            raise RuntimeError("Phase-2G evolution block generation-count drift")
        block_evaluations = int(block.get("classical_evaluations", -1))
        if block_evaluations != CLASSICAL_EVALUATIONS_PER_BLOCK:
            raise RuntimeError("Phase-2G evolution block classical-budget drift")
        if "population" not in block:
            raise RuntimeError("Phase-2G evolution block missing population")

        current = _freeze_population(
            block["population"], role=f"post-block-{start_generation}-{end_generation}"
        )
        classical_evaluations += block_evaluations
        block_events = block.get("selection_events", [])
        if not isinstance(block_events, list):
            raise RuntimeError("Phase-2G selection_events must be a list")
        selection_events.extend(block_events)

        checkpoint_records.append(
            {
                "checkpoint_generation": start_generation,
                "block_start_generation": start_generation,
                "block_end_generation": end_generation,
                "selection_enabled": bool(selection_enabled),
                "training_count": bundle_trainings,
                "curriculum_fingerprints": list(_population_fingerprints(curriculum)),
                "curriculum_digest_sha256": _population_digest(curriculum),
                "population_before_fingerprints": list(_population_fingerprints(before)),
                "population_after_fingerprints": list(_population_fingerprints(current)),
                "classical_evaluations": block_evaluations,
                "shuffle_rng_seed": (
                    int(shuffle_stream.rng_seed) if shuffle_stream is not None else None
                ),
            }
        )

    if len(checkpoint_records) != len(CHECKPOINT_GENERATIONS):
        raise RuntimeError("Phase-2G checkpoint count drift")
    if checkpoint_training_count != CHECKPOINT_TRAININGS_PER_CELL:
        raise RuntimeError("Phase-2G exact checkpoint training budget drift")
    if classical_evaluations != CLASSICAL_EVALUATIONS_PER_CELL:
        raise RuntimeError("Phase-2G exact classical evaluation budget drift")

    terminal = validate_sbox(select_terminal_classical_only(current))
    if terminal not in current:
        raise RuntimeError("Phase-2G terminal must come from the frozen final population")

    payload: dict[str, Any] = {
        "schema_version": 1,
        "phase": "2G",
        "arm": frozen_arm,
        "seed": frozen_seed,
        "generation_count": EVOLUTION_GENERATIONS,
        "classical_evaluations": classical_evaluations,
        "checkpoint_training_count": checkpoint_training_count,
        "initial_population_digest_sha256": _population_digest(initial),
        "terminal_population_digest_sha256": _population_digest(current),
        "terminal_sbox": list(terminal),
        "terminal_fingerprint": fingerprint_sbox(terminal),
        "terminal_selection_rule": "historical_classical_only",
        "checkpoints": checkpoint_records,
        "selection_events": selection_events,
        "heldout_accessed": False,
    }
    payload["scientific_payload_sha256"] = hashlib.sha256(_canonical(payload)).hexdigest()
    return payload
