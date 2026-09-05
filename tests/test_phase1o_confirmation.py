from __future__ import annotations

import pytest

from adversarial_sbox.experiment_seeds import (
    PHASE1O_CONFIRM_RESERVED_SEEDS,
    PHASE1O_DEV_SEEDS,
)
from adversarial_sbox.phase1o_confirm import (
    CONFIRMATION_REQUIRED_JOINT_SEEDS,
    aggregate_confirmation,
    run_confirmation_seed,
)


def _result(seed: int, *, joint_a: int, joint_b: int = 0, du_a: int = 8, du_b: int = 10):
    digest = f"digest-{seed}"
    return {
        "phase": "1O-confirm",
        "seed": seed,
        "initial_population_digest_sha256": digest,
        "arm_a": {
            "joint_target_count": joint_a,
            "du8_count": int(du_a <= 8),
            "best_du": du_a,
            "protected_classical_count": joint_a,
            "min_ito": 6.85,
            "classical_evaluations": 340,
            "initial_population_digest_sha256": digest,
        },
        "arm_b": {
            "joint_target_count": joint_b,
            "du8_count": int(du_b <= 8),
            "best_du": du_b,
            "protected_classical_count": joint_b,
            "min_ito": 6.84,
            "classical_evaluations": 340,
            "initial_population_digest_sha256": digest,
        },
        "arm_c": {
            "classical_evaluations": 340,
            "initial_population_digest_sha256": digest,
        },
        "deterministic_payload_match": True,
        "neural_oracle_executed": False,
    }


def test_confirmation_threshold_is_frozen_majority() -> None:
    assert CONFIRMATION_REQUIRED_JOINT_SEEDS == 5
    assert len(PHASE1O_CONFIRM_RESERVED_SEEDS) == 9


def test_confirmation_pass_requires_all_frozen_checks() -> None:
    seeds = PHASE1O_CONFIRM_RESERVED_SEEDS
    results = [
        _result(seed, joint_a=1 if index < 5 else 0)
        for index, seed in enumerate(seeds)
    ]
    aggregate = aggregate_confirmation(results)
    assert aggregate["verdict"] == "phase1o_confirm_pass"
    assert all(aggregate["confirmation_checks"].values())
    assert aggregate["summary"]["joint_seed_successes_a"] == 5


def test_confirmation_fails_when_only_four_of_nine_seeds_hit_joint() -> None:
    seeds = PHASE1O_CONFIRM_RESERVED_SEEDS
    results = [
        _result(seed, joint_a=1 if index < 4 else 0)
        for index, seed in enumerate(seeds)
    ]
    aggregate = aggregate_confirmation(results)
    assert aggregate["verdict"] == "phase1o_confirm_fail"
    assert aggregate["confirmation_checks"]["joint_seed_successes_ge_5"] is False


def test_confirmation_rejects_development_seed_before_execution() -> None:
    with pytest.raises(ValueError, match="confirmation seed"):
        run_confirmation_seed(PHASE1O_DEV_SEEDS[0])
