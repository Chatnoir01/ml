"""RED-first aggregation tests for the frozen Phase 2D support rule."""

from adversarial_sbox.phase2d_aggregate import (
    exact_one_sided_sign_p,
    protected_classical_key,
    summarize_support,
    transmission_plus2_rate,
)


def _lineage(fp: str, value):
    return {
        "generation": 1,
        "stage": "shortlist",
        "entered": [
            {
                "fingerprint": fp,
                "direct_plus_1": True,
                "descendant_plus_1": bool(value),
                "direct_plus_2": False if value is not None else None,
                "descendant_plus_2": value,
                "direct_plus_5": None,
                "descendant_plus_5": None,
                "terminal_self": False,
                "terminal_descendant": False,
            }
        ],
    }


def _classical(*, nl=100, du=8, lat=56, degree=7, sac=0.5):
    return {
        "nonlinearity": nl,
        "differential_uniformity": du,
        "max_linear_correlation": lat,
        "sac_score": sac,
        "algebraic_degree": degree,
        "fingerprint": f"x-{nl}-{du}-{lat}-{degree}",
    }


def test_transmission_rate_collapses_duplicate_fingerprints_by_logical_or_and_excludes_undefined():
    run = {
        "lineage_diagnostics": [
            _lineage("a", False),
            _lineage("a", True),
            _lineage("b", False),
            _lineage("c", None),
        ]
    }
    summary = transmission_plus2_rate(run)
    assert summary["defined_unique"] == 2
    assert summary["persistent_unique"] == 1
    assert summary["rate"] == 0.5


def test_zero_transmission_denominator_is_defined_as_zero_rate():
    summary = transmission_plus2_rate({"lineage_diagnostics": [_lineage("x", None)]})
    assert summary == {"defined_unique": 0, "persistent_unique": 0, "rate": 0.0}


def test_protected_classical_key_matches_absolute_priority_direction():
    stronger = protected_classical_key(_classical(nl=102))
    weaker = protected_classical_key(_classical(nl=100))
    assert stronger > weaker


def test_exact_one_sided_sign_test_excludes_ties_by_counts():
    assert exact_one_sided_sign_p(8, 1) < 0.05
    assert exact_one_sided_sign_p(6, 3) > 0.05
    assert exact_one_sided_sign_p(0, 0) == 1.0


def test_support_summary_requires_all_seven_preregistered_gates():
    o0 = [0.40] * 9
    op1 = [0.30] * 9
    sp1 = [0.35] * 9
    transmission_o0 = [0.0] * 9
    transmission_op1 = [0.5] * 9
    summary = summarize_support(
        o0=o0,
        op1=op1,
        sp1=sp1,
        transmission_o0=transmission_o0,
        transmission_op1=transmission_op1,
        classical_non_degradation=True,
    )
    assert summary["checks"] == {
        "mechanism_transmission_6_of_9": True,
        "op1_wins_o0_8_of_9": True,
        "paired_sign_p_lt_005": True,
        "mean_reduction_ge_002": True,
        "classical_non_degradation": True,
        "op1_wins_sp1_6_of_9": True,
        "op1_mean_lt_sp1_mean": True,
    }
    assert summary["verdict"] == "phase2d_bounded_persistence_supported"


def test_valid_prerequisites_but_one_failed_gate_yields_not_supported():
    summary = summarize_support(
        o0=[0.40] * 9,
        op1=[0.30] * 9,
        sp1=[0.25] * 9,
        transmission_o0=[0.0] * 9,
        transmission_op1=[0.5] * 9,
        classical_non_degradation=True,
    )
    assert summary["checks"]["op1_wins_sp1_6_of_9"] is False
    assert summary["verdict"] == "phase2d_bounded_persistence_not_supported"
