from adversarial_sbox.experiment_seeds import PHASE1I_CONFIRM_RESERVED_SEEDS
from adversarial_sbox.phase1i_confirmation import (
    aggregate_pairs,
    exact_one_sided_sign_p,
    selected_configuration,
)


def selection(name="c4_p96"):
    return {
        "experiment": "phase1i_frozen_development_selection",
        "selected_configuration": name,
        "development_gate": "pass",
        "confirmation_allowed": True,
    }


def pair(seed, *, outcome="directed", directed_adm=True, comparator_adm=False, directed_target=True, comparator_target=False, nl=100, du=8, corr=60, independent=True):
    side_base = {
        "unique_evaluations": 980,
        "best_metrics": {
            "nonlinearity": nl,
            "differential_uniformity": du,
            "max_linear_correlation": corr,
        },
    }
    return {
        "experiment": "phase1i_fresh_confirmation_pair",
        "selected_configuration": "c4_p96",
        "seed": seed,
        "outcome": outcome,
        "directed": {
            **side_base,
            "found_admissible": directed_adm,
            "found_structural_target": directed_target,
        },
        "comparator": {
            **side_base,
            "found_admissible": comparator_adm,
            "found_structural_target": comparator_target,
        },
        "independent_verification": {"pair_matches": independent},
    }


def test_sign_test_reference_values():
    assert exact_one_sided_sign_p(7, 0) == 0.0078125
    assert exact_one_sided_sign_p(0, 0) == 1.0


def test_invalid_selection_blocks_confirmation():
    invalid = selection()
    invalid["confirmation_allowed"] = False
    try:
        selected_configuration(invalid)
    except ValueError as error:
        assert "does not allow" in str(error)
    else:
        raise AssertionError("invalid selection should fail")


def test_all_twelve_frozen_checks_can_pass():
    pairs = [pair(seed) for seed in PHASE1I_CONFIRM_RESERVED_SEEDS]
    result = aggregate_pairs(selection=selection(), pairs=pairs)
    assert result["summary"]["verdict"] == "pass"
    assert result["summary"]["global_gate1"] == "green"
    assert result["summary"]["neural_oracle"] == "unblocked"
    assert all(result["summary"]["checks"].values())


def test_independent_mismatch_forces_fail():
    pairs = [pair(seed) for seed in PHASE1I_CONFIRM_RESERVED_SEEDS]
    pairs[0]["independent_verification"]["pair_matches"] = False
    result = aggregate_pairs(selection=selection(), pairs=pairs)
    assert result["summary"]["verdict"] == "fail"
    assert result["summary"]["global_gate1"] == "red"
    assert result["summary"]["checks"]["independent_verification_all_18_best_candidates"] is False
