from __future__ import annotations

import pytest

from adversarial_sbox.phase2h_timeline import build_divergence_timeline


def _arm(curricula: list[list[str]], populations: list[list[str]], prefix: str) -> dict:
    return {
        "checkpoints": [
            {
                "generation": generation,
                "curriculum_fingerprints": curriculum,
                "population_after_fingerprints": population,
                "training_receipt_sha256": (prefix + str(generation)).ljust(64, "0")[:64],
            }
            for generation, curriculum, population in zip(
                (0, 5, 10, 15), curricula, populations
            )
        ]
    }


def test_timeline_finds_first_divergence_without_guessing_between_checkpoints() -> None:
    fixed = _arm(
        [["x"], ["x"], ["x"], ["x"]],
        [["p0"], ["p5"], ["p10"], ["p15"]],
        "f",
    )
    adaptive = _arm(
        [["x"], ["a5"], ["a10"], ["a15"]],
        [["p0"], ["a5p"], ["a10p"], ["a15p"]],
        "a",
    )
    result = build_divergence_timeline(adaptive, fixed)
    assert result["first_curriculum_divergence_generation"] == 5
    assert result["first_population_divergence_generation"] == 5
    assert result["first_model_divergence_generation"] == 0
    assert result["earliest_divergence_generation"] == 0
    assert result["earliest_divergence_signals"] == ["model"]
    assert result["ordering_claim_available"] is True
    assert result["ordering_claim"] == "model_diverges_first"
    assert result["checkpoints"][0]["curriculum_jaccard"] == 1.0


def test_timeline_requires_complete_frozen_checkpoints() -> None:
    with pytest.raises(ValueError, match="incomplete"):
        build_divergence_timeline({"checkpoints": []}, {"checkpoints": []})


def test_timeline_refuses_ordering_claim_when_signals_tie_at_checkpoint() -> None:
    fixed = _arm(
        [["x"], ["x"], ["x"], ["x"]],
        [["p"], ["p"], ["p"], ["p"]],
        "z",
    )
    adaptive = _arm(
        [["x"], ["a"], ["a"], ["a"]],
        [["p"], ["q"], ["q"], ["q"]],
        "z",
    )
    # Keep model identity equal so curriculum/population are the first observable
    # divergences, tied at generation 5.
    result = build_divergence_timeline(adaptive, fixed)
    assert result["earliest_divergence_generation"] == 5
    assert result["earliest_divergence_signals"] == ["curriculum", "population"]
    assert result["ordering_claim_available"] is False
    assert result["ordering_claim"] is None
    assert "cannot order signals" in result["ordering_note"]


def test_missing_curriculum_is_unknown_not_fake_equal() -> None:
    fixed = _arm([["x"]] * 4, [["p"]] * 4, "z")
    adaptive = _arm([["x"]] * 4, [["p"]] * 4, "z")
    for arm in (adaptive, fixed):
        for row in arm["checkpoints"]:
            row.pop("curriculum_fingerprints")
    result = build_divergence_timeline(adaptive, fixed)
    assert result["checkpoints"][0]["curriculum_same"] is None
    assert result["checkpoints"][0]["curriculum_jaccard"] is None
    assert result["first_curriculum_divergence_generation"] is None
    assert result["ordering_claim"] is None


def test_missing_identity_prevents_false_first_cause_ordering() -> None:
    fixed = _arm([["x"]] * 4, [["p"]] * 4, "f")
    adaptive = _arm([["x"]] * 4, [["p"]] * 4, "a")
    adaptive["checkpoints"][0].pop("curriculum_fingerprints")
    result = build_divergence_timeline(adaptive, fixed)
    assert result["earliest_divergence_generation"] == 0
    assert result["earliest_divergence_signals"] == ["model"]
    assert result["ordering_claim_available"] is False
    assert result["ordering_unresolved_due_to_missing_evidence"] is True
    assert result["ordering_claim"] is None


def test_duplicate_checkpoint_rejected_instead_of_overwriting_receipt() -> None:
    fixed = _arm([["x"]] * 4, [["p"]] * 4, "z")
    adaptive = _arm([["x"]] * 4, [["p"]] * 4, "a")
    adaptive["checkpoints"].append(dict(adaptive["checkpoints"][0]))
    with pytest.raises(ValueError, match="duplicate checkpoint"):
        build_divergence_timeline(adaptive, fixed)


def test_duplicate_or_malformed_checkpoint_fingerprints_are_rejected() -> None:
    fixed = _arm([["x"]] * 4, [["p"]] * 4, "z")
    adaptive = _arm([["x"]] * 4, [["p"]] * 4, "a")
    adaptive["checkpoints"][0]["curriculum_fingerprints"] = ["x", "x"]
    with pytest.raises(ValueError, match="duplicate curriculum fingerprint"):
        build_divergence_timeline(adaptive, fixed)
    adaptive["checkpoints"][0]["curriculum_fingerprints"] = "x"
    with pytest.raises(ValueError, match="invalid curriculum fingerprint evidence"):
        build_divergence_timeline(adaptive, fixed)


def test_missing_population_with_same_values_does_not_claim_equivalence() -> None:
    fixed = _arm([["x"]] * 4, [["p"]] * 4, "z")
    adaptive = _arm([["x"]] * 4, [["p"]] * 4, "z")
    adaptive["checkpoints"][0].pop("population_after_fingerprints")
    result = build_divergence_timeline(adaptive, fixed)
    assert result["checkpoints"][0]["population_after_same"] is None
    assert result["checkpoints"][0]["population_after_jaccard"] is None
