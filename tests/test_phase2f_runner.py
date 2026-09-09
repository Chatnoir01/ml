"""Phase 2F runner tests; no real neural training is executed."""

import inspect
import random

from adversarial_sbox.evolution import ClassicalMetrics, HardConstraints
from adversarial_sbox.phase1m import _initial_population, _population_digest
from adversarial_sbox.phase1o import _run_multihotspot_arm
from adversarial_sbox.phase2f import SHUFFLE_SEED_OFFSET
from adversarial_sbox.phase2f_runner import (
    Phase2FScoreLedger,
    cutoff_order,
    make_shuffled_control_rng,
    run_arm,
)
import adversarial_sbox.phase2f_runner as phase2f_runner


def _metrics(name: str, *, nl: int = 104, du: int = 8, lat: int = 56, degree: int = 7):
    return ClassicalMetrics(
        nonlinearity=nl,
        differential_uniformity=du,
        max_linear_correlation=lat,
        sac_score=0.5,
        algebraic_degree=degree,
        fingerprint=name,
    )


def _fake_sbox(tag: int):
    values = list(range(256))
    values[0], values[tag] = values[tag], values[0]
    return tuple(values)


def _fake_scorer(sbox):
    from adversarial_sbox.provenance import fingerprint_sbox

    return {
        "purpose": "fitness",
        "fingerprint": fingerprint_sbox(sbox),
        "training_count": 16,
        "neural_advantage": float(sbox[0]) / 255.0,
        "scientific_payload_sha256": f"phase2f-fake-{sbox[0]}",
        "runs": [{"synthetic": True, "index": i} for i in range(16)],
    }


def test_runner_source_cannot_import_or_name_heldout_block_x_paths():
    source = inspect.getsource(phase2f_runner)
    assert "phase2f_validation" not in source
    assert "VALIDATION_DATASET_SEEDS" not in source
    assert "VALIDATION_MODEL_SEEDS" not in source
    assert "Block X scoring" in source


def test_shuffled_control_rng_is_one_persistent_stream_from_frozen_offset():
    seed = 526011
    rng = make_shuffled_control_rng(seed)
    reference = random.Random(seed + SHUFFLE_SEED_OFFSET)
    assert [rng.random() for _ in range(12)] == [reference.random() for _ in range(12)]
    assert inspect.getsource(run_arm).count("make_shuffled_control_rng") == 1


def test_score_ledger_enforces_hard_cap_and_retains_receipts():
    ledger = Phase2FScoreLedger(_fake_scorer, budget=2)
    left, right, extra = _fake_sbox(1), _fake_sbox(2), _fake_sbox(3)
    ledger.score(left)
    ledger.score(right)
    assert ledger.score_count == 2
    assert ledger.training_count == 32
    assert len(ledger.receipts[0].score_payload["runs"]) == 16
    try:
        ledger.score(extra)
    except RuntimeError:
        pass
    else:
        raise AssertionError("Phase 2F score budget must be hard")


def test_b1_band_is_never_partially_scored():
    constraints = HardConstraints()
    a, b = _fake_sbox(2), _fake_sbox(1)
    metrics = {a: _metrics("a", nl=104), b: _metrics("b", nl=102)}
    ledger = Phase2FScoreLedger(_fake_scorer, budget=1)
    events = []
    ordered = cutoff_order(
        [a, b],
        metrics=metrics,
        constraints=constraints,
        cutoff=1,
        arm="B1",
        oracle=ledger,
        shuffle_rng=None,
        generation=0,
        stage="shortlist",
        audit_events=events,
    )
    assert ordered == [a, b]
    assert ledger.score_count == 0
    assert ledger.selection_closed is True
    assert events[-1]["event"] == "score_budget_closed"


def test_b1_records_real_cross_protected_key_membership_change():
    constraints = HardConstraints()
    cutoff_candidate, entering = _fake_sbox(2), _fake_sbox(1)
    metrics = {
        cutoff_candidate: _metrics("cut", nl=104),
        entering: _metrics("enter", nl=102),
    }
    ledger = Phase2FScoreLedger(_fake_scorer, budget=2)
    events = []
    ordered = cutoff_order(
        [cutoff_candidate, entering],
        metrics=metrics,
        constraints=constraints,
        cutoff=1,
        arm="B1",
        oracle=ledger,
        shuffle_rng=None,
        generation=0,
        stage="shortlist",
        audit_events=events,
    )
    assert ordered[0] == entering
    event = events[-1]
    assert event["membership_changed"] is True
    assert event["cross_protected_key_membership_change"] is True
    assert len(event["score_caused_entered"]) == 1


def test_control_arm_replays_confirmed_phase1o_and_terminal_is_classical_only():
    seed = 526011
    initial = _initial_population(seed)
    digest = _population_digest(initial)
    historical = _run_multihotspot_arm(initial, seed=seed, initial_digest=digest)
    control = run_arm(seed=seed, arm="C", scorer=_fake_scorer)
    assert control["initial_population_digest_sha256"] == digest
    assert control["classical_evaluations"] == historical["classical_evaluations"] == 340
    assert control["proposal_audit_sha256"] == historical["proposal_audit_sha256"]
    assert control["oracle_candidate_scores"] == 32
    assert control["oracle_fitness_trainings"] == 512
    assert control["terminal_selection_rule"] == "historical_classical_only"
    best = historical["best_feasibility_metrics"]
    terminal = control["terminal_classical"]
    assert terminal["fingerprint"] == best["fingerprint"]


def test_runner_emits_band_and_lineage_instrumentation_without_validation_values():
    result = run_arm(seed=526011, arm="B1", scorer=_fake_scorer)
    assert result["schema_version"] == 1
    assert result["phase"] == "2F"
    assert result["arm"] == "B1"
    assert result["classical_evaluations"] == 340
    assert result["oracle_candidate_scores"] == 32
    assert result["oracle_fitness_trainings"] == 512
    assert isinstance(result["selection_events"], list)
    assert isinstance(result["generation_trace"], list)
    assert len(result["generation_trace"]) == 20
    assert "validation" not in result
    assert "block_x" not in result
    assert all("cutoff_reference_metrics" in event for event in result["selection_events"])
