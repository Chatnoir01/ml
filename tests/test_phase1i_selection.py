from adversarial_sbox.phase1i import CONFIGURATIONS
from adversarial_sbox.phase1i_selection import select_from_documents


def document(name, *, adm=0, target=0, comp_adm=0, comp_target=0, wins=0, comp_wins=0, nl=98, du=10, corr=60, first=None):
    return {
        "experiment": "phase1i_fresh_population_vns_batch_development",
        "configuration": {"name": name},
        "summary": {
            "directed_admissible_runs": adm,
            "directed_target_runs": target,
            "comparator_admissible_runs": comp_adm,
            "comparator_target_runs": comp_target,
            "directed_wins": wins,
            "comparator_wins": comp_wins,
            "median_nonlinearity_directed": nl,
            "median_du_directed": du,
            "median_max_corr_directed": corr,
            "median_first_admissible_evaluation": first,
        },
    }


def full_batch(**overrides):
    docs = []
    for name in CONFIGURATIONS:
        kwargs = overrides.get(name, {})
        docs.append(document(name, **kwargs))
    return docs


def test_no_eligible_configuration_blocks_confirmation():
    result = select_from_documents(full_batch())
    assert result["development_gate"] == "fail"
    assert result["selected_configuration"] is None
    assert result["confirmation_allowed"] is False


def test_more_admissible_runs_wins_before_secondary_metrics():
    docs = full_batch(
        c2_p96={"adm": 2, "target": 5, "wins": 5, "nl": 104, "du": 6, "corr": 48, "first": 500},
        c3_p96={"adm": 3, "target": 3, "wins": 3, "nl": 100, "du": 8, "corr": 64, "first": 900},
    )
    result = select_from_documents(docs)
    assert result["selected_configuration"] == "c3_p96"


def test_declaration_order_breaks_complete_tie():
    equal = {"adm": 2, "target": 2, "wins": 2, "nl": 100, "du": 8, "corr": 60, "first": 700}
    docs = full_batch(c2_p96=equal, c3_p96=equal)
    result = select_from_documents(docs)
    assert result["selected_configuration"] == "c2_p96"
