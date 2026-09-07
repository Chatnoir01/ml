"""RED-first contract for Phase 2D bounded one-generation persistence."""

import random
from pathlib import Path

from adversarial_sbox.evolution import ClassicalMetrics, HardConstraints, primary_security_key
from adversarial_sbox.phase2_evolution_seed_registry import (
    PHASE2D_RESERVED_EVOLUTION_SEEDS,
    phase2d_evolution_seeds_are_fresh,
    reserved_evolution_seed_registry_through_phase2b,
)
from adversarial_sbox.phase2_neural_seed_registry import (
    complete_seed_registry_through_phase2b,
    phase2d_reserved_blocks,
)
from adversarial_sbox.phase2d import (
    ARCHITECTURE,
    ARMS,
    DEPTH,
    DIFFERENCES,
    EVOLUTION_SEEDS,
    FITNESS_DATASET_SEEDS,
    FITNESS_MODEL_SEEDS,
    FITNESS_TRAININGS_PER_ARM_SEED,
    ORACLE_SCORE_BUDGET_PER_ARM_SEED,
    ORACLE_TRAININGS_PER_SCORE,
    PAIR_COUNT,
    SPLIT_SIZES,
    VALIDATION_DATASET_SEEDS,
    VALIDATION_MODEL_SEEDS,
    PersistenceLedger,
    apply_phase2d_order,
    phase2d_verdict,
)


def _metrics(*, nl: int = 100, du: int = 8, lat: int = 56, degree: int = 7, sac: float = 0.5):
    return ClassicalMetrics(
        nonlinearity=nl,
        differential_uniformity=du,
        max_linear_correlation=lat,
        sac_score=sac,
        algebraic_degree=degree,
        fingerprint=f"m-{nl}-{du}-{lat}-{degree}-{sac}",
    )


def test_phase2d_frozen_contract_and_exact_budgets():
    assert ARCHITECTURE == "byte_tanh_mlp"
    assert DEPTH == 4
    assert DIFFERENCES == (0x00000001, 0x00000100)
    assert PAIR_COUNT == 8192
    assert SPLIT_SIZES == (5734, 1228, 1230)
    assert ARMS == ("C", "O0", "OP1", "SP1")
    assert EVOLUTION_SEEDS == (426011, 426023, 426037, 426049, 426061, 426073, 426089, 426101, 426113)
    assert FITNESS_DATASET_SEEDS == (376003, 376017, 376031, 376043, 376057, 376069, 376081, 376093)
    assert FITNESS_MODEL_SEEDS == (386009, 386021, 386033, 386047, 386059, 386071, 386087, 386099)
    assert VALIDATION_DATASET_SEEDS == (476003, 476017, 476029, 476043, 476057, 476071, 476083, 476099)
    assert VALIDATION_MODEL_SEEDS == (486007, 486019, 486031, 486043, 486061, 486073, 486091, 486103)
    assert ORACLE_TRAININGS_PER_SCORE == 16
    assert ORACLE_SCORE_BUDGET_PER_ARM_SEED == 32
    assert FITNESS_TRAININGS_PER_ARM_SEED == 512


def test_phase2d_evolution_seeds_are_centrally_reserved_fresh_and_unique():
    assert EVOLUTION_SEEDS == PHASE2D_RESERVED_EVOLUTION_SEEDS
    assert len(EVOLUTION_SEEDS) == len(set(EVOLUTION_SEEDS)) == 9
    assert phase2d_evolution_seeds_are_fresh(EVOLUTION_SEEDS)
    assert set(EVOLUTION_SEEDS).isdisjoint(reserved_evolution_seed_registry_through_phase2b())


def test_phase2d_neural_blocks_are_fresh_and_mutually_disjoint():
    prior = set(complete_seed_registry_through_phase2b())
    blocks = phase2d_reserved_blocks()
    assert tuple(name for name, _dataset, _model in blocks) == ("phase2d-fitness-F", "phase2d-validation-W")
    fitness = set(FITNESS_DATASET_SEEDS) | set(FITNESS_MODEL_SEEDS)
    validation = set(VALIDATION_DATASET_SEEDS) | set(VALIDATION_MODEL_SEEDS)
    assert fitness.isdisjoint(prior)
    assert validation.isdisjoint(prior)
    assert fitness.isdisjoint(validation)
    assert len(fitness) == 16
    assert len(validation) == 16


def test_marker_gated_workflow_keeps_block_w_out_of_preflight():
    workflow = Path(".github/workflows/phase2d.yml").read_text(encoding="utf-8")
    preflight = workflow.split("\n  preflight:\n", 1)[1].split("\n  arm:\n", 1)[0]
    for forbidden in (
        "VALIDATION_DATASET_SEEDS",
        "VALIDATION_MODEL_SEEDS",
        "TOTAL_HELDOUT_TRAININGS",
        "validation_seed_gate",
        "phase2d_validation",
        "phase2d_validation_seeds",
    ):
        assert forbidden not in preflight


def test_persistence_can_never_cross_a_better_protected_classical_key():
    constraints = HardConstraints()
    stronger = _metrics(nl=102)
    weaker = _metrics(nl=100)
    assert primary_security_key(stronger, constraints) > primary_security_key(weaker, constraints)
    ordered = apply_phase2d_order(
        [("stronger", stronger, 0.90), ("weaker", weaker, 0.01)],
        constraints=constraints,
        arm="OP1",
        active_tags={"weaker"},
        shuffle_rng=None,
    )
    assert ordered[0][0] == "stronger"


def test_active_persistence_tag_precedes_score_only_inside_exact_key_group():
    constraints = HardConstraints()
    left = _metrics(sac=0.49)
    right = _metrics(sac=0.51)
    assert primary_security_key(left, constraints) == primary_security_key(right, constraints)
    ordered = apply_phase2d_order(
        [("left", left, 0.90), ("right", right, 0.01)],
        constraints=constraints,
        arm="OP1",
        active_tags={"left"},
        shuffle_rng=None,
    )
    assert [item[0] for item in ordered] == ["left", "right"]


def test_o0_has_no_persistence_and_matches_tie_only_oracle_semantics():
    constraints = HardConstraints()
    left = _metrics(sac=0.49)
    right = _metrics(sac=0.51)
    ordered = apply_phase2d_order(
        [("left", left, 0.30), ("right", right, 0.10)],
        constraints=constraints,
        arm="O0",
        active_tags={"left"},
        shuffle_rng=None,
    )
    assert [item[0] for item in ordered] == ["right", "left"]


def test_sp1_uses_same_tag_priority_but_persistent_shuffled_rng_for_scores():
    constraints = HardConstraints()
    items = [("a", _metrics(sac=0.48), 0.1), ("b", _metrics(sac=0.49), 0.2), ("c", _metrics(sac=0.50), 0.3)]
    rng = random.Random(24680)
    reference = random.Random(24680)
    first = apply_phase2d_order(items, constraints=constraints, arm="SP1", active_tags={"b"}, shuffle_rng=rng)
    replay = apply_phase2d_order(items, constraints=constraints, arm="SP1", active_tags={"b"}, shuffle_rng=reference)
    assert first == replay
    assert first[0][0] == "b"


def test_persistence_ledger_expires_after_exactly_one_next_generation_stage_and_does_not_stack():
    ledger = PersistenceLedger()
    ledger.create(fingerprint="x", generation=4, stage="survival")
    ledger.create(fingerprint="x", generation=4, stage="survival")
    assert ledger.active(generation=5, stage="survival") == frozenset({"x"})
    assert ledger.active(generation=5, stage="shortlist") == frozenset()
    ledger.finish_stage(generation=5, stage="survival")
    assert ledger.active(generation=6, stage="survival") == frozenset()


def test_persistence_ledger_rejects_tags_not_created_by_membership_entry():
    ledger = PersistenceLedger()
    ledger.create_from_membership_change(
        generation=2,
        stage="shortlist",
        entered=(),
        ordering_changed=True,
    )
    assert ledger.active(generation=3, stage="shortlist") == frozenset()
    ledger.create_from_membership_change(
        generation=2,
        stage="shortlist",
        entered=("entrant",),
        ordering_changed=True,
    )
    assert ledger.active(generation=3, stage="shortlist") == frozenset({"entrant"})


def test_phase2d_verdict_requires_every_preregistered_support_gate():
    checks = {
        "mechanism_transmission_6_of_9": True,
        "op1_wins_o0_8_of_9": True,
        "paired_sign_p_lt_005": True,
        "mean_reduction_ge_002": True,
        "classical_non_degradation": True,
        "op1_wins_sp1_6_of_9": True,
        "op1_mean_lt_sp1_mean": True,
    }
    assert phase2d_verdict(True, checks) == "phase2d_bounded_persistence_supported"
    failed = dict(checks)
    failed["mechanism_transmission_6_of_9"] = False
    assert phase2d_verdict(True, failed) == "phase2d_bounded_persistence_not_supported"
    assert phase2d_verdict(False, checks) == "phase2d_inconclusive_prerequisites"
