"""RED-first Phase 2D runner tests; no neural training is executed."""

import inspect
import random

from adversarial_sbox.evolution import ClassicalMetrics, HardConstraints
from adversarial_sbox.phase1m import _initial_population, _population_digest
from adversarial_sbox.phase1o import _run_multihotspot_arm
from adversarial_sbox.phase2d import SHUFFLE_SEED_OFFSET
from adversarial_sbox.phase2d_runner import (
    Phase2DScoreLedger,
    cutoff_order,
    make_shuffled_control_rng,
    run_arm,
)
import adversarial_sbox.phase2d_runner as phase2d_runner


def _metrics(name: str, *, nl: int = 100, du: int = 8, lat: int = 56, degree: int = 7):
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
        "scientific_payload_sha256": f"phase2d-fake-{sbox[0]}",
        "runs": [{"synthetic": True, "index": i} for i in range(16)],
    }


def test_runner_source_cannot_import_or_name_heldout_block_w_paths():
    source = inspect.getsource(phase2d_runner)
    assert "phase2d_validation" not in source
    assert "VALIDATION_DATASET_SEEDS" not in source
    assert "VALIDATION_MODEL_SEEDS" not in source
    assert "Block W" not in source


def test_shuffled_control_rng_is_one_persistent_stream_from_frozen_offset():
    seed = 426011
    rng = make_shuffled_control_rng(seed)
    reference = random.Random(seed + SHUFFLE_SEED_OFFSET)
    assert [rng.random() for _ in range(12)] == [reference.random() for _ in range(12)]
    assert inspect.getsource(run_arm).count("make_shuffled_control_rng") == 1


def test_score_ledger_enforces_hard_cap_and_retains_receipts():
    ledger = Phase2DScoreLedger(_fake_scorer, budget=2)
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
        raise AssertionError("Phase 2D score budget must be hard")


def test_boundary_group_is_never_partially_scored():
    constraints = HardConstraints()
    a, b, c = _fake_sbox(1), _fake_sbox(2), _fake_sbox(3)
    metrics = {a: _metrics("a"), b: _metrics("b"), c: _metrics("c")}
    ledger = Phase2DScoreLedger(_fake_scorer, budget=1)
    events = []
    cutoff_order(
        [a, b, c],
        metrics=metrics,
        constraints=constraints,
        cutoff=1,
        arm="OP1",
        oracle=ledger,
        shuffle_rng=None,
        generation=0,
        stage="shortlist",
        persistence=None,
        audit_events=events,
    )
    assert ledger.score_count == 0
    assert ledger.selection_closed is True
    assert any(event["event"] == "score_budget_closed" for event in events)


def test_op1_membership_entry_creates_one_next_generation_same_stage_tag():
    from adversarial_sbox.phase2d import PersistenceLedger

    constraints = HardConstraints()
    a, b, c = _fake_sbox(1), _fake_sbox(2), _fake_sbox(3)
    metrics = {a: _metrics("a"), b: _metrics("b"), c: _metrics("c")}
    ledger = Phase2DScoreLedger(_fake_scorer, budget=3)
    persistence = PersistenceLedger()
    events = []
    ordered = cutoff_order(
        [c, b, a],
        metrics=metrics,
        constraints=constraints,
        cutoff=1,
        arm="OP1",
        oracle=ledger,
        shuffle_rng=None,
        generation=2,
        stage="shortlist",
        persistence=persistence,
        audit_events=events,
    )
    assert ordered[0] == a
    from adversarial_sbox.provenance import fingerprint_sbox
    assert persistence.active(generation=3, stage="shortlist") == frozenset({fingerprint_sbox(a)})
    assert persistence.active(generation=3, stage="survival") == frozenset()


def test_post_closure_opportunity_is_observational_only_even_with_active_tag():
    from adversarial_sbox.phase2d import PersistenceLedger
    from adversarial_sbox.provenance import fingerprint_sbox

    constraints = HardConstraints()
    a, b = _fake_sbox(1), _fake_sbox(2)
    metrics = {a: _metrics("a"), b: _metrics("b")}
    ledger = Phase2DScoreLedger(_fake_scorer, budget=1)
    ledger.close_selection()
    persistence = PersistenceLedger()
    persistence.create(fingerprint=fingerprint_sbox(b), generation=0, stage="shortlist")
    ordered = cutoff_order(
        [a, b],
        metrics=metrics,
        constraints=constraints,
        cutoff=1,
        arm="OP1",
        oracle=ledger,
        shuffle_rng=None,
        generation=1,
        stage="shortlist",
        persistence=persistence,
        audit_events=[],
    )
    assert ordered == [a, b]
    assert persistence.active(generation=2, stage="shortlist") == frozenset()


def test_control_arm_replays_confirmed_phase1o_fighter_and_exact_budget_with_fake_scores():
    seed = 426011
    initial = _initial_population(seed)
    digest = _population_digest(initial)
    historical = _run_multihotspot_arm(initial, seed=seed, initial_digest=digest)
    control = run_arm(seed=seed, arm="C", scorer=_fake_scorer)
    assert control["initial_population_digest_sha256"] == digest
    assert control["classical_evaluations"] == historical["classical_evaluations"] == 340
    assert control["proposal_audit_sha256"] == historical["proposal_audit_sha256"]
    assert control["oracle_candidate_scores"] == 32
    assert control["oracle_fitness_trainings"] == 512
    best = historical["best_feasibility_metrics"]
    terminal = control["terminal_classical"]
    assert terminal["fingerprint"] == best["fingerprint"]


def test_runner_emits_tag_and_lineage_instrumentation_without_validation_values():
    result = run_arm(seed=426011, arm="OP1", scorer=_fake_scorer)
    assert result["schema_version"] == 1
    assert result["phase"] == "2D"
    assert result["arm"] == "OP1"
    assert result["classical_evaluations"] == 340
    assert result["oracle_candidate_scores"] == 32
    assert result["oracle_fitness_trainings"] == 512
    assert isinstance(result["selection_events"], list)
    assert isinstance(result["generation_trace"], list)
    assert len(result["generation_trace"]) == 20
    assert "validation" not in result
    assert "block_w" not in result
