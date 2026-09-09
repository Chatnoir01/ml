from __future__ import annotations

import inspect
from pathlib import Path

from adversarial_sbox.phase2f import SUPPORT_CHECKS
from adversarial_sbox.phase2f_aggregate import (
    componentwise_classical_non_degradation,
    exact_one_sided_sign_p,
    mechanism_activity,
    summarize_support,
)
from adversarial_sbox.phase2f_validation import validation_seed_gate
import adversarial_sbox.phase2f_runner as runner


def _classical(*, nl=104, du=8, lat=56, degree=7, sac=0.5, fp="x"):
    return {
        "nonlinearity": nl,
        "differential_uniformity": du,
        "max_linear_correlation": lat,
        "algebraic_degree": degree,
        "sac_score": sac,
        "fingerprint": fp,
    }


def test_exact_sign_test_matches_preregistered_one_sided_rule():
    assert exact_one_sided_sign_p(9, 0) == 1 / 512
    assert exact_one_sided_sign_p(8, 1) == 10 / 512
    assert exact_one_sided_sign_p(0, 0) == 1.0


def test_classical_non_degradation_is_componentwise_not_lexicographic():
    control = _classical(nl=104, du=8, lat=56, degree=7)
    assert componentwise_classical_non_degradation(
        _classical(nl=106, du=6, lat=54, degree=7), control
    )
    # Better NL cannot compensate for worse DU under the frozen gate.
    assert not componentwise_classical_non_degradation(
        _classical(nl=108, du=10, lat=54, degree=7), control
    )
    assert not componentwise_classical_non_degradation(
        _classical(nl=106, du=6, lat=58, degree=7), control
    )
    assert not componentwise_classical_non_degradation(
        _classical(nl=106, du=6, lat=54, degree=6), control
    )


def test_mechanism_activity_counts_only_scored_cross_key_membership_changes():
    run = {
        "selection_events": [
            {"scored": True, "membership_changed": True, "cross_protected_key_membership_change": True},
            {"scored": True, "membership_changed": True, "cross_protected_key_membership_change": False},
            {"scored": False, "membership_changed": True, "cross_protected_key_membership_change": True},
        ]
    }
    result = mechanism_activity(run)
    assert result["active"] is True
    assert result["cross_key_membership_changes"] == 1
    assert result["event_indices"] == [0]


def test_support_requires_all_seven_frozen_gates():
    # Eight B1 wins over O0, 6/9 activity, >=.02 mean reduction, and six SB1 wins.
    o0 = [0.40] * 9
    b1 = [0.36] * 8 + [0.40]
    sb1 = [0.39] * 6 + [0.35] * 3
    support = summarize_support(
        o0=o0,
        b1=b1,
        sb1=sb1,
        mechanism_active=[True] * 6 + [False] * 3,
        classical_non_degradation=True,
    )
    assert set(support["checks"]) == set(SUPPORT_CHECKS)
    assert support["checks"]["mechanism_activity_6_of_9"] is True
    assert support["checks"]["b1_wins_o0_8_of_9"] is True
    assert support["checks"]["paired_sign_p_lt_005"] is True
    assert support["checks"]["mean_reduction_ge_002"] is True
    assert support["checks"]["classical_non_degradation"] is True
    assert support["checks"]["b1_wins_sb1_6_of_9"] is True
    assert support["checks"]["b1_mean_lt_sb1_mean"] is True
    assert support["verdict"] == "phase2f_minimal_band_pressure_supported"


def test_one_red_support_gate_forces_not_supported():
    support = summarize_support(
        o0=[0.40] * 9,
        b1=[0.39] * 9,
        sb1=[0.41] * 9,
        mechanism_active=[True] * 9,
        classical_non_degradation=True,
    )
    assert support["checks"]["mean_reduction_ge_002"] is False
    assert support["verdict"] == "phase2f_minimal_band_pressure_not_supported"


def test_block_x_is_physically_absent_from_evolution_runner_and_seed_gate_is_green():
    source = inspect.getsource(runner)
    assert "phase2f_validation" not in source
    assert "VALIDATION_DATASET_SEEDS" not in source
    assert "VALIDATION_MODEL_SEEDS" not in source
    assert validation_seed_gate()


def test_scientific_workflow_is_marker_gated_and_marker_fail_closed():
    workflow = Path('.github/workflows/phase2f.yml').read_text(encoding='utf-8')
    assert "research/PHASE2F_EXECUTE.md" in workflow
    assert "AUTHORIZED_PHASE2F_MINIMAL_BAND_EXPERIMENT" in workflow
    assert "needs: terminal_freeze" in workflow
    marker = Path('research/PHASE2F_EXECUTE.md')
    if marker.exists():
        assert marker.read_text(encoding='utf-8').strip() == "AUTHORIZED_PHASE2F_MINIMAL_BAND_EXPERIMENT"
