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
    assert result["checkpoints"][0]["curriculum_jaccard"] == 1.0


def test_timeline_requires_complete_frozen_checkpoints() -> None:
    with pytest.raises(ValueError, match="incomplete"):
        build_divergence_timeline({"checkpoints": []}, {"checkpoints": []})
