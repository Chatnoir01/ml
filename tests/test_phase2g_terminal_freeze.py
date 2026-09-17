"""RED contract for Phase 2G terminal freeze and held-out H blindness.

These tests are synthetic only. They do not train models, run evolution, or touch
held-out data. The implementation under test must freeze all 36 terminal cells
before any held-out H evaluation can be authorized.
"""

from __future__ import annotations

import copy
import hashlib
import json

import pytest

from adversarial_sbox.phase2g import (
    ARMS,
    CHECKPOINT_GENERATIONS,
    EVOLUTION_SEEDS,
    SCORING_DATASET_BASE_SEEDS,
    TRAINING_DATASET_BASE_SEEDS,
    TRAINING_MODEL_BASE_SEEDS,
    expanded_checkpoint_seed_block,
)
from adversarial_sbox.phase2g_terminal_freeze import (
    CLASSICAL_EVALUATIONS_PER_CELL,
    freeze_phase2g_terminals,
    heldout_h_authorized,
)
from adversarial_sbox.provenance import fingerprint_sbox


def _sbox(offset: int) -> list[int]:
    return list(range(offset, 256)) + list(range(offset))


def _sha_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _population_digest(fingerprints: list[str]) -> str:
    return hashlib.sha256("\n".join(fingerprints).encode("ascii")).hexdigest()


def _with_scientific_receipt(payload: dict[str, object]) -> dict[str, object]:
    frozen = dict(payload)
    raw = json.dumps(frozen, sort_keys=True, separators=(",", ":")).encode("utf-8")
    frozen["scientific_payload_sha256"] = hashlib.sha256(raw).hexdigest()
    return frozen


def _rehash_cell(cell: dict[str, object]) -> None:
    clean = {key: value for key, value in cell.items() if key != "scientific_payload_sha256"}
    raw = json.dumps(clean, sort_keys=True, separators=(",", ":")).encode("utf-8")
    cell["scientific_payload_sha256"] = hashlib.sha256(raw).hexdigest()


def _provenance(seed: int, arm: str, terminal_fingerprint: str, arm_index: int) -> dict[str, object]:
    initial = [_sha_text(f"{seed}:matched-initial:{index}") for index in range(20)]
    current = list(initial)
    generation_trace: list[dict[str, object]] = []
    classical_ledger: list[dict[str, object]] = []
    parent_map: dict[str, str] = {}

    def ledger_row(fingerprint: str, *, terminal: bool = False) -> dict[str, object]:
        return {
            "fingerprint": fingerprint,
            "nonlinearity": 100 + arm_index if terminal else 100,
            "differential_uniformity": 8,
            "max_abs_lat": 32,
            "sac_score": 0.5,
            "algebraic_degree": 7,
        }

    classical_ledger.extend(ledger_row(fingerprint) for fingerprint in initial)
    checkpoint_populations: dict[int, list[str]] = {}
    checkpoint_after: dict[int, list[str]] = {}

    for generation in range(20):
        population_before = list(current)
        if generation in CHECKPOINT_GENERATIONS:
            checkpoint_populations[generation] = list(population_before)
        shortlist = list(population_before[:8])
        parents = list(shortlist[:4])
        proposals = [
            _sha_text(f"{seed}:{arm}:proposal:{generation}:{index}")
            for index in range(16)
        ]
        if generation == 19:
            proposals[0] = terminal_fingerprint
        for index, proposal in enumerate(proposals):
            parent_map[proposal] = parents[index % len(parents)]
            classical_ledger.append(
                ledger_row(proposal, terminal=proposal == terminal_fingerprint)
            )
        next_population = [*population_before[:4], *proposals]
        generation_trace.append(
            {
                "generation": generation,
                "population_before": population_before,
                "shortlist": shortlist,
                "parents": parents,
                "proposals": proposals,
                "next_population": next_population,
            }
        )
        current = next_population
        if generation in (4, 9, 14, 19):
            checkpoint_after[generation - 4] = list(current)

    checkpoints: list[dict[str, object]] = []
    for checkpoint_index, generation in enumerate(CHECKPOINT_GENERATIONS):
        t_seeds = list(
            expanded_checkpoint_seed_block(TRAINING_DATASET_BASE_SEEDS, checkpoint_index)
        )
        m_seeds = list(
            expanded_checkpoint_seed_block(TRAINING_MODEL_BASE_SEEDS, checkpoint_index)
        )
        q_seeds = list(
            expanded_checkpoint_seed_block(SCORING_DATASET_BASE_SEEDS, checkpoint_index)
        )
        curriculum = (
            list(initial) if arm == "F" else list(checkpoint_populations[generation])
        )
        model_receipts = [
            {
                "difference": difference,
                "replicate": replicate,
                "dataset_seed": t_seeds[replicate],
                "model_seed": m_seeds[replicate],
                "state_sha256": _sha_text(
                    f"{seed}:{arm}:{generation}:{difference}:{replicate}:state"
                ),
            }
            for difference in (1, 256)
            for replicate in range(8)
        ]
        checkpoints.append(
            {
                "generation": generation,
                "checkpoint_generation": generation,
                "block_start_generation": generation,
                "block_end_generation": generation + 5,
                "selection_enabled": arm != "C",
                "training_count": 16,
                "training_receipt_sha256": _sha_text(
                    f"{seed}:{arm}:{generation}:training"
                ),
                "curriculum_fingerprints": curriculum,
                "curriculum_digest_sha256": _population_digest(curriculum),
                "population_before_fingerprints": list(checkpoint_populations[generation]),
                "population_after_fingerprints": list(checkpoint_after[generation]),
                "classical_evaluations": 80,
                "shuffle_rng_seed": (
                    int(_sha_text(f"shuffle:{seed}:{generation}")[:16], 16)
                    if arm == "S"
                    else None
                ),
                "training_dataset_seeds": t_seeds,
                "training_model_seeds": m_seeds,
                "scoring_dataset_seeds": q_seeds,
                "model_receipts": model_receipts,
                "score_cache_hits": 0,
                "score_cache_misses": 0,
                "score_receipts": [],
            }
        )

    assert len(classical_ledger) == 340
    assert len({row["fingerprint"] for row in classical_ledger}) == 340
    assert terminal_fingerprint in current
    return {
        "generation_count": 20,
        "checkpoint_training_count": 64,
        "terminal_population_digest_sha256": _population_digest(current),
        "heldout_accessed": False,
        "selection_events": [],
        "generation_trace": generation_trace,
        "classical_evaluation_ledger": classical_ledger,
        "parent_map": parent_map,
        "lineage_diagnostics": [],
        "checkpoints": checkpoints,
        "initial_population_digest_sha256": _population_digest(initial),
    }


def _cell(seed: int, arm: str, arm_index: int) -> dict[str, object]:
    sbox = _sbox((seed + arm_index) % 256)
    terminal_fingerprint = fingerprint_sbox(sbox)
    provenance = _provenance(seed, arm, terminal_fingerprint, arm_index)
    return _with_scientific_receipt(
        {
            "schema_version": 1,
            "phase": "2G",
            "seed": seed,
            "arm": arm,
            "classical_evaluations": 340,
            "checkpoint_trainings": 64,
            **provenance,
            "terminal_selection_rule": "historical_classical_only",
            "terminal_fingerprint": terminal_fingerprint,
            "terminal_sbox": sbox,
            "terminal_classical": {
                "admissible": True,
                "nonlinearity": 100 + arm_index,
                "differential_uniformity": 8,
                "max_abs_lat": 32,
                "algebraic_degree": 7,
            },
        }
    )


def _cells() -> list[dict[str, object]]:
    return [
        _cell(seed, arm, arm_index)
        for seed in EVOLUTION_SEEDS
        for arm_index, arm in enumerate(ARMS)
    ]


def test_frozen_budget_identity_is_exact() -> None:
    assert CLASSICAL_EVALUATIONS_PER_CELL == 340
    assert len(ARMS) * len(EVOLUTION_SEEDS) == 36


def test_freeze_requires_exact_36_cells_and_is_deterministic() -> None:
    cells = _cells()
    forward = freeze_phase2g_terminals(cells)
    reverse = freeze_phase2g_terminals(list(reversed(cells)))

    assert forward == reverse
    assert forward["phase"] == "2G-terminal-freeze"
    assert forward["cell_count"] == 36
    assert forward["checkpoint_training_count"] == 36 * 64
    assert forward["heldout_training_count"] == 0
    assert forward["heldout_accessed"] is False
    assert len(forward["terminal_freeze_sha256"]) == 64
    assert heldout_h_authorized(forward) is True


def test_freeze_fails_closed_on_missing_or_duplicate_cell() -> None:
    cells = _cells()
    with pytest.raises(ValueError):
        freeze_phase2g_terminals(cells[:-1])
    with pytest.raises(ValueError):
        freeze_phase2g_terminals(cells + [copy.deepcopy(cells[0])])


def test_freeze_fails_closed_on_budget_checkpoint_or_terminal_rule_drift() -> None:
    for field, value in (
        ("classical_evaluations", 339),
        ("checkpoint_trainings", 63),
        ("terminal_selection_rule", "neural_rerank"),
    ):
        cells = _cells()
        cells[0][field] = value
        with pytest.raises(ValueError):
            freeze_phase2g_terminals(cells)

    cells = _cells()
    cells[0]["checkpoints"] = list(cells[0]["checkpoints"])[:-1]
    with pytest.raises(ValueError):
        freeze_phase2g_terminals(cells)


def test_freeze_rejects_scientific_receipt_tamper() -> None:
    cells = _cells()
    cells[0]["terminal_classical"]["nonlinearity"] = 1
    with pytest.raises(ValueError, match="scientific payload receipt mismatch"):
        freeze_phase2g_terminals(cells)


def test_freeze_rejects_mismatched_initial_population_across_matched_arms() -> None:
    cells = _cells()
    cells[0]["initial_population_digest_sha256"] = "a" * 64
    _rehash_cell(cells[0])
    with pytest.raises(ValueError, match="matched arms"):
        freeze_phase2g_terminals(cells)


def test_freeze_rejects_rehashed_missing_cell_provenance() -> None:
    for field in (
        "generation_trace",
        "classical_evaluation_ledger",
        "parent_map",
        "lineage_diagnostics",
    ):
        cells = _cells()
        cells[0].pop(field)
        _rehash_cell(cells[0])
        with pytest.raises(ValueError, match="provenance"):
            freeze_phase2g_terminals(cells)

    cells = _cells()
    cells[0]["checkpoints"][0].pop("scoring_dataset_seeds")
    _rehash_cell(cells[0])
    with pytest.raises(ValueError, match="provenance"):
        freeze_phase2g_terminals(cells)


def test_h_authorization_fails_closed_on_any_freeze_tamper() -> None:
    frozen = freeze_phase2g_terminals(_cells())
    for field, value in (
        ("cell_count", 35),
        ("heldout_accessed", True),
        ("heldout_training_count", 1),
        ("terminal_freeze_sha256", "0" * 64),
    ):
        tampered = copy.deepcopy(frozen)
        tampered[field] = value
        assert heldout_h_authorized(tampered) is False
