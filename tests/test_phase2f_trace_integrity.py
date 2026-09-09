"""RED-first tests for Phase 2F generation-trace structural integrity."""

from adversarial_sbox.phase2f_trace_integrity import generation_record_report


def _record():
    population = [f"p{i}" for i in range(20)]
    shortlist = population[:8]
    parents = shortlist[:4]
    proposals = [
        {"proposal_fingerprint": f"c{i}", "parent_fingerprint": parents[i % 4]}
        for i in range(16)
    ]
    return {
        "generation": 0,
        "population_before": population,
        "shortlist": shortlist,
        "parents": parents,
        "proposals": proposals,
        "next_population": population[:4] + [f"c{i}" for i in range(16)],
    }


def test_valid_generation_record_passes_structural_gate():
    report = generation_record_report(_record(), expected_generation=0, prior_candidates=set())
    assert report["pass"] is True


def test_proposal_parent_must_be_one_of_recorded_parents():
    record = _record()
    record["proposals"][0]["parent_fingerprint"] = "not-a-parent"
    report = generation_record_report(record, expected_generation=0, prior_candidates=set())
    assert report["pass"] is False
    assert report["checks"]["proposal_parentage"] is False


def test_duplicate_or_previously_seen_proposal_fails_closed():
    record = _record()
    record["proposals"][1]["proposal_fingerprint"] = record["proposals"][0]["proposal_fingerprint"]
    report = generation_record_report(record, expected_generation=0, prior_candidates=set())
    assert report["pass"] is False
    assert report["checks"]["proposal_uniqueness"] is False

    record = _record()
    report = generation_record_report(record, expected_generation=0, prior_candidates={"c0"})
    assert report["pass"] is False
    assert report["checks"]["proposal_uniqueness"] is False


def test_next_population_cannot_contain_unrealized_candidate():
    record = _record()
    record["next_population"][0] = "ghost"
    report = generation_record_report(record, expected_generation=0, prior_candidates=set())
    assert report["pass"] is False
    assert report["checks"]["survivor_pool"] is False
