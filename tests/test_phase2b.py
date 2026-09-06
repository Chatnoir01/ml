"""RED-first scientific contract for Phase 2B GA <- frozen Neural Oracle pressure."""

from adversarial_sbox.evolution import ClassicalMetrics, HardConstraints, primary_security_key
from adversarial_sbox.phase2b import (
    ARCHITECTURE,
    DEPTH,
    DIFFERENCES,
    EVOLUTION_SEEDS,
    FITNESS_DATASET_SEEDS,
    FITNESS_MODEL_SEEDS,
    PAIR_COUNT,
    SPLIT_SIZES,
    VALIDATION_DATASET_SEEDS,
    VALIDATION_MODEL_SEEDS,
    apply_oracle_tiebreak,
    phase2b_verdict,
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


def test_phase2b_frozen_contract():
    assert ARCHITECTURE == "byte_tanh_mlp"
    assert DEPTH == 4
    assert DIFFERENCES == (0x00000001, 0x00000100)
    assert PAIR_COUNT == 8192
    assert SPLIT_SIZES == (5734, 1228, 1230)
    assert EVOLUTION_SEEDS == (326011, 326023, 326033, 326047, 326051, 326063, 326071, 326087, 326099)
    assert FITNESS_DATASET_SEEDS == (176003, 176017, 176029, 176041, 176057, 176069, 176081, 176093)
    assert FITNESS_MODEL_SEEDS == (186007, 186019, 186031, 186043, 186061, 186073, 186091, 186103)
    assert VALIDATION_DATASET_SEEDS == (276003, 276017, 276029, 276041, 276053, 276067, 276079, 276091)
    assert VALIDATION_MODEL_SEEDS == (286007, 286019, 286031, 286043, 286057, 286069, 286081, 286103)


def test_neural_score_cannot_cross_protected_classical_key():
    constraints = HardConstraints()
    stronger = _metrics(nl=102)
    weaker = _metrics(nl=100)
    assert primary_security_key(stronger, constraints) > primary_security_key(weaker, constraints)

    ordered = apply_oracle_tiebreak(
        [("stronger", stronger, 0.90), ("weaker", weaker, 0.01)],
        constraints=constraints,
        mode="oracle",
        shuffle_seed=1,
    )
    assert ordered[0][0] == "stronger"


def test_real_oracle_only_breaks_exact_classical_ties_toward_lower_signal():
    constraints = HardConstraints()
    left = _metrics(sac=0.49)
    right = _metrics(sac=0.51)
    assert primary_security_key(left, constraints) == primary_security_key(right, constraints)

    ordered = apply_oracle_tiebreak(
        [("left", left, 0.30), ("right", right, 0.10)],
        constraints=constraints,
        mode="oracle",
        shuffle_seed=7,
    )
    assert ordered[0][0] == "right"


def test_control_ignores_oracle_scores():
    constraints = HardConstraints()
    left = _metrics(sac=0.49)
    right = _metrics(sac=0.51)
    ordered = apply_oracle_tiebreak(
        [("left", left, 0.90), ("right", right, 0.01)],
        constraints=constraints,
        mode="control",
        shuffle_seed=7,
    )
    assert [item[0] for item in ordered] == ["left", "right"]


def test_phase2b_verdict_requires_every_preregistered_support_gate():
    checks = {
        "o_wins_c_8_of_9": True,
        "paired_sign_p_lt_005": True,
        "mean_reduction_ge_002": True,
        "classical_non_degradation": True,
        "o_wins_s_6_of_9": True,
        "o_reduction_gt_s_reduction": True,
    }
    assert phase2b_verdict(True, checks) == "phase2b_oracle_pressure_supported"
    failed = dict(checks)
    failed["classical_non_degradation"] = False
    assert phase2b_verdict(True, failed) == "phase2b_oracle_pressure_not_supported"
    assert phase2b_verdict(False, checks) == "phase2b_inconclusive_prerequisites"
