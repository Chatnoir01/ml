"""RED-first runner plumbing tests for Phase 2B; no neural training is executed."""

import inspect
import random

from adversarial_sbox.evolution import ClassicalMetrics, HardConstraints
from adversarial_sbox.phase1m import _initial_population, _population_digest
from adversarial_sbox.phase1o import _run_multihotspot_arm
from adversarial_sbox.phase2b import SHUFFLE_SEED_OFFSET
from adversarial_sbox.phase2b_runner import (
    OracleScoreLedger,
    cutoff_order,
    make_shuffled_control_rng,
    run_arm,
)
import adversarial_sbox.phase2b_runner as phase2b_runner


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
    # Stable low-dimensional fake score; runner tests never train a network.
    score = float(sbox[0]) / 255.0
    from adversarial_sbox.provenance import fingerprint_sbox
    return {
        "purpose": "fitness",
        "fingerprint": fingerprint_sbox(sbox),
        "training_count": 16,
        "neural_advantage": score,
        "scientific_payload_sha256": f"fake-{sbox[0]}",
    }


def test_runner_source_cannot_import_held_out_validation_module():
    assert "phase2b_validation" not in inspect.getsource(phase2b_runner)


def test_shuffled_control_rng_is_initialized_once_from_exact_preregistered_seed_offset():
    seed = 326011
    rng = make_shuffled_control_rng(seed)
    reference = random.Random(seed + SHUFFLE_SEED_OFFSET)
    assert [rng.random() for _ in range(12)] == [reference.random() for _ in range(12)]

    source = inspect.getsource(phase2b_runner.run_arm)
    assert source.count("make_shuffled_control_rng") == 1
    assert "generation * 2" not in source


def test_oracle_ledger_enforces_exact_candidate_score_cap():
    ledger = OracleScoreLedger(_fake_scorer, budget=2)
    left = _fake_sbox(1)
    right = _fake_sbox(2)
    ledger.score(left)
    ledger.score(right)
    assert ledger.score_count == 2
    assert ledger.training_count == 32
    try:
        ledger.score(_fake_sbox(3))
    except RuntimeError:
        pass
    else:
        raise AssertionError("Oracle score budget must be hard")


def test_cutoff_oracle_scores_only_complete_exact_key_boundary_group():
    constraints = HardConstraints()
    strong = _fake_sbox(1)
    tied_a = _fake_sbox(2)
    tied_b = _fake_sbox(3)
    metrics = {
        strong: _metrics("strong", nl=102),
        tied_a: _metrics("a"),
        tied_b: _metrics("b"),
    }
    ledger = OracleScoreLedger(_fake_scorer, budget=2)
    ordered = cutoff_order(
        [tied_b, strong, tied_a],
        metrics=metrics,
        constraints=constraints,
        cutoff=2,
        mode="oracle",
        oracle=ledger,
        shuffle_rng=None,
    )
    assert ordered[0] == strong
    assert set(ordered[1:]) == {tied_a, tied_b}
    assert ledger.score_count == 2


def test_boundary_group_is_not_partially_scored_when_budget_cannot_fit_it():
    constraints = HardConstraints()
    a, b, c = _fake_sbox(1), _fake_sbox(2), _fake_sbox(3)
    metrics = {a: _metrics("a"), b: _metrics("b"), c: _metrics("c")}
    ledger = OracleScoreLedger(_fake_scorer, budget=1)
    cutoff_order(
        [a, b, c],
        metrics=metrics,
        constraints=constraints,
        cutoff=1,
        mode="oracle",
        oracle=ledger,
        shuffle_rng=None,
    )
    assert ledger.score_count == 0


def test_shuffled_ties_consume_one_persistent_rng_stream():
    constraints = HardConstraints()
    a, b, c = _fake_sbox(1), _fake_sbox(2), _fake_sbox(3)
    d, e, f = _fake_sbox(4), _fake_sbox(5), _fake_sbox(6)
    metrics = {
        a: _metrics("a"), b: _metrics("b"), c: _metrics("c"),
        d: _metrics("d"), e: _metrics("e"), f: _metrics("f"),
    }
    ledger = OracleScoreLedger(_fake_scorer, budget=6)
    rng = make_shuffled_control_rng(326011)

    first = cutoff_order(
        [a, b, c], metrics=metrics, constraints=constraints, cutoff=1,
        mode="shuffled", oracle=ledger, shuffle_rng=rng,
    )
    second = cutoff_order(
        [d, e, f], metrics=metrics, constraints=constraints, cutoff=1,
        mode="shuffled", oracle=ledger, shuffle_rng=rng,
    )

    # Replaying from one identically seeded RNG must reproduce both calls in sequence.
    replay_ledger = OracleScoreLedger(_fake_scorer, budget=6)
    replay_rng = make_shuffled_control_rng(326011)
    assert first == cutoff_order(
        [a, b, c], metrics=metrics, constraints=constraints, cutoff=1,
        mode="shuffled", oracle=replay_ledger, shuffle_rng=replay_rng,
    )
    assert second == cutoff_order(
        [d, e, f], metrics=metrics, constraints=constraints, cutoff=1,
        mode="shuffled", oracle=replay_ledger, shuffle_rng=replay_rng,
    )


def test_control_arm_replays_confirmed_phase1o_fighter_exactly():
    seed = 326011
    initial = _initial_population(seed)
    digest = _population_digest(initial)
    historical = _run_multihotspot_arm(initial, seed=seed, initial_digest=digest)
    control = run_arm(seed=seed, mode="control", scorer=_fake_scorer)

    assert control["initial_population_digest_sha256"] == digest
    assert control["classical_evaluations"] == historical["classical_evaluations"] == 340
    assert control["proposal_audit_sha256"] == historical["proposal_audit_sha256"]

    best = historical["best_feasibility_metrics"]
    terminal = control["terminal_classical"]
    assert terminal["nonlinearity"] == best["nonlinearity"]
    assert terminal["differential_uniformity"] == best["differential_uniformity"]
    assert terminal["max_linear_correlation"] == best["max_linear_correlation"]
    assert terminal["algebraic_degree"] == best["algebraic_degree"]
    assert terminal["fingerprint"] == best["fingerprint"]
