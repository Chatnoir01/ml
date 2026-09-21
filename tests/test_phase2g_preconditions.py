from dataclasses import FrozenInstanceError

import pytest

from adversarial_sbox.phase2g import EVOLUTION_SEEDS
from adversarial_sbox.phase2g_preconditions import (
    AdaptationSeedEvidence,
    classify_adaptation_activity,
    make_s_shuffle_stream,
    s_shuffle_seed,
)


def _digest(value: int) -> str:
    return f"{value:064x}"


def test_s_shuffle_seed_matches_frozen_sha256_derivation():
    # sha256(b"phase2g:S:726011:5")[:8], interpreted unsigned big-endian.
    assert s_shuffle_seed(726011, 5) == 4957567298020245467
    assert s_shuffle_seed(726011, 0) == 9586493424061858639

    with pytest.raises(ValueError):
        s_shuffle_seed(123, 5)
    with pytest.raises(ValueError):
        s_shuffle_seed(726011, 6)


def test_s_shuffle_stream_is_persistent_deterministic_and_receipted():
    stream_a = make_s_shuffle_stream(726011, 5)
    stream_b = make_s_shuffle_stream(726011, 5)

    first_a = stream_a.shuffle_assignment(("a", "b", "c", "d"), (0.1, 0.2, 0.3, 0.4))
    second_a = stream_a.shuffle_assignment(("e", "f", "g", "h"), (0.5, 0.6, 0.7, 0.8))
    first_b = stream_b.shuffle_assignment(("a", "b", "c", "d"), (0.1, 0.2, 0.3, 0.4))
    second_b = stream_b.shuffle_assignment(("e", "f", "g", "h"), (0.5, 0.6, 0.7, 0.8))

    assert first_a == first_b
    assert second_a == second_b
    assert first_a.rng_seed == 4957567298020245467
    assert first_a.draw_index == 0
    assert second_a.draw_index == 1
    assert sorted(score for _fp, score in first_a.after) == [0.1, 0.2, 0.3, 0.4]
    assert tuple(fp for fp, _score in first_a.after) == ("a", "b", "c", "d")
    assert len(first_a.receipt_sha256) == 64

    with pytest.raises(FrozenInstanceError):
        first_a.rng_seed = 1


def _evidence(*, curriculum_changed_count: int, ordering_changed_count: int):
    rows = []
    for index, seed in enumerate(EVOLUTION_SEEDS):
        initial = _digest(1000 + index)
        if index < curriculum_changed_count:
            checkpoint_digests = (initial, _digest(2000 + index), initial)
        else:
            checkpoint_digests = (initial, initial, initial)
        rows.append(
            AdaptationSeedEvidence(
                evolution_seed=seed,
                initial_curriculum_digest_sha256=initial,
                adaptive_checkpoint_curriculum_digests_sha256=checkpoint_digests,
                different_a_vs_f_ordering_in_fully_eligible_b1=(index < ordering_changed_count),
            )
        )
    return tuple(rows)


def test_adaptation_activity_requires_both_preregistered_six_of_nine_conditions():
    passed = classify_adaptation_activity(
        _evidence(curriculum_changed_count=6, ordering_changed_count=6)
    )
    assert passed.curriculum_changed_seed_count == 6
    assert passed.score_ordering_changed_seed_count == 6
    assert passed.passes is True

    curriculum_short = classify_adaptation_activity(
        _evidence(curriculum_changed_count=5, ordering_changed_count=9)
    )
    assert curriculum_short.passes is False

    ordering_short = classify_adaptation_activity(
        _evidence(curriculum_changed_count=9, ordering_changed_count=5)
    )
    assert ordering_short.passes is False


def test_adaptation_activity_fails_closed_on_missing_or_duplicate_seed_evidence():
    full = list(_evidence(curriculum_changed_count=9, ordering_changed_count=9))
    with pytest.raises(ValueError):
        classify_adaptation_activity(full[:-1])

    duplicate = list(full)
    duplicate[-1] = duplicate[0]
    with pytest.raises(ValueError):
        classify_adaptation_activity(duplicate)
