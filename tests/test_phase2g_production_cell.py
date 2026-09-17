"""RED contract for concrete Phase 2G scientific-cell composition.

All expensive work is dependency-injected with deterministic synthetic doubles.
The test requires the production composition path to wire the real checkpoint
bundle, GA adapter and complete arm runner without accessing held-out H.
"""

from __future__ import annotations

import hashlib
import json
from types import SimpleNamespace

from adversarial_sbox.evolution import ClassicalMetrics
from adversarial_sbox.phase2g import EVOLUTION_SEEDS
from adversarial_sbox.phase2g_experiment import run_phase2g_scientific_cell
from adversarial_sbox.phase2g_ga_adapter import Phase2GGABlockAdapter
from adversarial_sbox.provenance import fingerprint_sbox


def _canonical(payload):
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha(payload) -> str:
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _population(_seed: int):
    base = list(range(256))
    return tuple(tuple(base[offset:] + base[:offset]) for offset in range(20))


def _evaluator(candidate):
    return ClassicalMetrics(
        nonlinearity=104,
        differential_uniformity=4,
        max_linear_correlation=32,
        sac_score=0.5,
        algebraic_degree=6,
        fingerprint=fingerprint_sbox(candidate),
    )


def _parents(shortlist, _metrics):
    return tuple(shortlist[:4])


def _proposals(*, parents, rng, seen_ever, count):
    assert len(parents) == 4
    assert count == 16
    out = []
    while len(out) < count:
        values = list(range(256))
        rng.shuffle(values)
        candidate = tuple(values)
        if candidate in seen_ever or candidate in out:
            continue
        out.append(candidate)
    return tuple(out)


def _adapter_factory(*, arm, evolution_seed, score_ledger_factory):
    return Phase2GGABlockAdapter(
        arm=arm,
        evolution_seed=evolution_seed,
        evaluator=_evaluator,
        parent_selector=_parents,
        proposal_factory=_proposals,
        score_ledger_factory=score_ledger_factory,
    )


def test_concrete_phase2g_cell_composes_real_checkpoint_and_ga_interfaces():
    train_calls = []
    score_calls = []

    def train_model(**kwargs):
        curriculum = tuple(kwargs["curriculum"])
        digest = _sha(
            "\n".join(fingerprint_sbox(candidate) for candidate in curriculum).encode("ascii")
        )
        train_calls.append(
            (
                kwargs["arm"],
                kwargs["evolution_seed"],
                kwargs["checkpoint_generation"],
                kwargs["difference"],
                kwargs["replicate"],
            )
        )
        return SimpleNamespace(
            arm=kwargs["arm"],
            evolution_seed=kwargs["evolution_seed"],
            checkpoint_generation=kwargs["checkpoint_generation"],
            difference=kwargs["difference"],
            replicate=kwargs["replicate"],
            dataset_seed=kwargs["dataset_seed"],
            model_seed=kwargs["model_seed"],
            curriculum_digest_sha256=digest,
            state_sha256=_sha(
                f"model:{kwargs['arm']}:{kwargs['evolution_seed']}:{kwargs['checkpoint_generation']}:{kwargs['difference']}:{kwargs['replicate']}"
            ),
        )

    def score_candidate(candidate, *, models):
        model = models[0]
        fingerprint = fingerprint_sbox(candidate)
        score_calls.append(
            (model.arm, model.evolution_seed, model.checkpoint_generation, fingerprint)
        )
        payload = {
            "arm": model.arm,
            "evolution_seed": model.evolution_seed,
            "checkpoint_generation": model.checkpoint_generation,
            "candidate_fingerprint": fingerprint,
            "model_count": len(models),
            "training_count": 0,
            "neural_advantage": (int(fingerprint[:8], 16) % 10000) / 10000.0,
        }
        payload["scientific_payload_sha256"] = hashlib.sha256(_canonical(payload)).hexdigest()
        return payload

    result = run_phase2g_scientific_cell(
        seed=EVOLUTION_SEEDS[0],
        arm="A",
        initial_population_factory=_population,
        train_model=train_model,
        score_candidate=score_candidate,
        ga_adapter_factory=_adapter_factory,
    )

    assert result["phase"] == "2G"
    assert result["arm"] == "A"
    assert result["generation_count"] == 20
    assert result["classical_evaluations"] == 340
    assert result["checkpoint_trainings"] == 64
    assert result["checkpoint_training_count"] == 64
    assert result["terminal_selection_rule"] == "historical_classical_only"
    assert result["heldout_accessed"] is False
    assert len(result["checkpoints"]) == 4
    assert [row["generation"] for row in result["checkpoints"]] == [0, 5, 10, 15]
    assert all(row["training_count"] == 16 for row in result["checkpoints"])
    assert len(train_calls) == 64
    assert score_calls
    assert result["selection_events"]
    assert set(result["terminal_classical"]) == {
        "admissible",
        "nonlinearity",
        "differential_uniformity",
        "max_abs_lat",
        "algebraic_degree",
    }
    assert len(result["terminal_sbox"]) == 256
    assert len(result["scientific_payload_sha256"]) == 64


def test_concrete_control_cell_records_audit_scores_but_never_changes_selection():
    train_count = 0
    score_count = 0

    def train_model(**kwargs):
        nonlocal train_count
        train_count += 1
        curriculum = tuple(kwargs["curriculum"])
        digest = _sha(
            "\n".join(fingerprint_sbox(candidate) for candidate in curriculum).encode("ascii")
        )
        return SimpleNamespace(
            arm=kwargs["arm"],
            evolution_seed=kwargs["evolution_seed"],
            checkpoint_generation=kwargs["checkpoint_generation"],
            difference=kwargs["difference"],
            replicate=kwargs["replicate"],
            dataset_seed=kwargs["dataset_seed"],
            model_seed=kwargs["model_seed"],
            curriculum_digest_sha256=digest,
            state_sha256=_sha(
                f"control-model:{kwargs['checkpoint_generation']}:{kwargs['difference']}:{kwargs['replicate']}"
            ),
        )

    def score_candidate(candidate, *, models):
        nonlocal score_count
        score_count += 1
        model = models[0]
        fingerprint = fingerprint_sbox(candidate)
        payload = {
            "arm": model.arm,
            "evolution_seed": model.evolution_seed,
            "checkpoint_generation": model.checkpoint_generation,
            "candidate_fingerprint": fingerprint,
            "model_count": len(models),
            "training_count": 0,
            "neural_advantage": (int(fingerprint[:8], 16) % 10000) / 10000.0,
        }
        payload["scientific_payload_sha256"] = hashlib.sha256(_canonical(payload)).hexdigest()
        return payload

    result = run_phase2g_scientific_cell(
        seed=EVOLUTION_SEEDS[0],
        arm="C",
        initial_population_factory=_population,
        train_model=train_model,
        score_candidate=score_candidate,
        ga_adapter_factory=_adapter_factory,
    )

    assert train_count == 64
    assert score_count > 0
    assert result["checkpoint_trainings"] == 64
    opportunities = [event for event in result["selection_events"] if event["boundary_opportunity"]]
    assert opportunities
    assert all(event["neural_selection_enabled"] is False for event in opportunities)
    assert all(event["scored_candidate_count"] == len(event["b1_group"]) for event in opportunities)
    assert all(event["assigned_scores"] for event in opportunities)
    assert all(event["selected_before"] == event["selected_after"] for event in opportunities)
    assert all(event["membership_changed"] is False for event in opportunities)
