from __future__ import annotations

import pytest

from adversarial_sbox.phase2g_curriculum import freeze_checkpoint_curriculum
from adversarial_sbox.provenance import fingerprint_sbox


def rotated_sbox(offset: int) -> tuple[int, ...]:
    offset = int(offset) % 256
    return tuple((value + offset) % 256 for value in range(256))


def population(start: int) -> tuple[tuple[int, ...], ...]:
    return tuple(rotated_sbox(start + index) for index in range(20))


def canonical(items):
    return tuple(sorted(items, key=fingerprint_sbox))


def test_fixed_arm_always_freezes_exact_initial_population():
    initial = population(1)
    current = population(41)

    for checkpoint in (0, 5, 10, 15):
        frozen = freeze_checkpoint_curriculum(
            arm="F",
            checkpoint_generation=checkpoint,
            initial_population=initial,
            current_population=current,
        )
        assert frozen == canonical(initial)
        assert set(frozen).isdisjoint(current)


def test_adaptive_and_audit_arms_freeze_exact_current_population():
    initial = population(1)
    current = population(41)

    for arm in ("C", "A", "S"):
        frozen = freeze_checkpoint_curriculum(
            arm=arm,
            checkpoint_generation=10,
            initial_population=initial,
            current_population=current,
        )
        assert frozen == canonical(current)
        assert set(frozen).isdisjoint(initial)


def test_curriculum_is_canonical_independent_of_input_order():
    initial = population(1)
    current = population(41)
    reverse_current = tuple(reversed(current))

    one = freeze_checkpoint_curriculum(
        arm="A",
        checkpoint_generation=5,
        initial_population=initial,
        current_population=current,
    )
    two = freeze_checkpoint_curriculum(
        arm="A",
        checkpoint_generation=5,
        initial_population=initial,
        current_population=reverse_current,
    )
    assert one == two == canonical(current)


def test_curriculum_contract_fails_closed_on_protocol_drift():
    initial = population(1)
    current = population(41)

    with pytest.raises(ValueError):
        freeze_checkpoint_curriculum(
            arm="X",
            checkpoint_generation=5,
            initial_population=initial,
            current_population=current,
        )

    with pytest.raises(ValueError):
        freeze_checkpoint_curriculum(
            arm="A",
            checkpoint_generation=7,
            initial_population=initial,
            current_population=current,
        )

    with pytest.raises(ValueError):
        freeze_checkpoint_curriculum(
            arm="A",
            checkpoint_generation=5,
            initial_population=initial[:-1],
            current_population=current,
        )

    duplicate_current = (*current[:-1], current[0])
    with pytest.raises(ValueError):
        freeze_checkpoint_curriculum(
            arm="A",
            checkpoint_generation=5,
            initial_population=initial,
            current_population=duplicate_current,
        )
