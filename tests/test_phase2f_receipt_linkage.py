"""RED-first tests for Phase 2F score-event/Block-G receipt linkage."""

from adversarial_sbox.phase2f_receipt_linkage import arm_score_linkage_report


def _run(arm="B1"):
    receipts = [
        {"fingerprint": "a", "neural_advantage": 0.30, "role": "selection"},
        {"fingerprint": "b", "neural_advantage": 0.10, "role": "selection"},
    ]
    assigned = {"a": 0.30, "b": 0.10}
    return {
        "arm": arm,
        "oracle_receipts": receipts,
        "selection_events": [
            {
                "scored": True,
                "base_group": ["a", "b"],
                "assigned_scores": assigned,
                "score_caused_entered": ["b"] if arm != "C" else [],
            }
        ],
    }


def test_real_score_assignment_links_exactly_to_block_g_receipts():
    assert arm_score_linkage_report(_run("B1"))["pass"] is True


def test_score_assignment_drift_fails_closed_even_if_event_is_self_consistent():
    run = _run("B1")
    run["selection_events"][0]["assigned_scores"]["a"] = 0.20
    report = arm_score_linkage_report(run)
    assert report["pass"] is False
    assert report["checks"]["assigned_scores_match_receipts"] is False


def test_missing_receipt_for_scored_candidate_fails_closed():
    run = _run("O0")
    run["oracle_receipts"] = run["oracle_receipts"][:1]
    report = arm_score_linkage_report(run)
    assert report["pass"] is False
    assert report["checks"]["scored_candidates_have_receipts"] is False


def test_sb1_must_preserve_exact_score_multiset_under_shuffle():
    run = _run("SB1")
    run["selection_events"][0]["assigned_scores"] = {"a": 0.10, "b": 0.30}
    assert arm_score_linkage_report(run)["pass"] is True
    run["selection_events"][0]["assigned_scores"] = {"a": 0.10, "b": 0.20}
    report = arm_score_linkage_report(run)
    assert report["pass"] is False
    assert report["checks"]["assigned_scores_match_receipts"] is False


def test_selection_receipts_must_be_exercised_by_recorded_score_events():
    run = _run("B1")
    run["oracle_receipts"].append(
        {"fingerprint": "unused", "neural_advantage": 0.05, "role": "selection"}
    )
    report = arm_score_linkage_report(run)
    assert report["pass"] is False
    assert report["checks"]["selection_receipts_are_exercised"] is False
