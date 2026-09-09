from __future__ import annotations

import random

import pytest

from adversarial_sbox.evolution import ClassicalMetrics, HardConstraints
from adversarial_sbox.phase2f import (
    ARMS,
    EVOLUTION_SEEDS,
    FITNESS_DATASET_SEEDS,
    FITNESS_MODEL_SEEDS,
    SUPPORT_CHECKS,
    apply_phase2f_cutoff_order,
    in_b1_band,
    phase2f_verdict,
)
from adversarial_sbox.phase2f_validation_seeds import (
    VALIDATION_DATASET_SEEDS,
    VALIDATION_MODEL_SEEDS,
)
from adversarial_sbox.phase2_evolution_seed_registry import (
    PHASE2F_RESERVED_EVOLUTION_SEEDS,
    phase2f_evolution_seeds_are_fresh,
)
from adversarial_sbox.phase2_neural_seed_registry import registry_is_disjoint


def m(*, nl=104, du=8, lat=64, degree=6, sac=0.5, fp="x"):
    return ClassicalMetrics(
        nonlinearity=nl,
        differential_uniformity=du,
        max_linear_correlation=lat,
        sac_score=sac,
        algebraic_degree=degree,
        fingerprint=fp,
    )


def test_phase2f_frozen_identity_and_fresh_seeds():
    assert ARMS == ("C", "O0", "B1", "SB1")
    assert EVOLUTION_SEEDS == (
        526011,
        526023,
        526037,
        526049,
        526061,
        526073,
        526087,
        526099,
        526111,
    )
    assert EVOLUTION_SEEDS == PHASE2F_RESERVED_EVOLUTION_SEEDS
    assert phase2f_evolution_seeds_are_fresh(EVOLUTION_SEEDS)
    assert FITNESS_DATASET_SEEDS == (
        576003,
        576017,
        576031,
        576043,
        576059,
        576071,
        576083,
        576097,
    )
    assert FITNESS_MODEL_SEEDS == (
        586009,
        586021,
        586033,
        586047,
        586061,
        586073,
        586087,
        586099,
    )
    assert VALIDATION_DATASET_SEEDS == (
        676003,
        676017,
        676029,
        676043,
        676057,
        676071,
        676083,
        676099,
    )
    assert VALIDATION_MODEL_SEEDS == (
        686007,
        686019,
        686031,
        686043,
        686061,
        686073,
        686091,
        686103,
    )
    assert registry_is_disjoint(FITNESS_DATASET_SEEDS, FITNESS_MODEL_SEEDS, before="phase2f")
    assert registry_is_disjoint(VALIDATION_DATASET_SEEDS, VALIDATION_MODEL_SEEDS, before="phase2f")
    assert set(FITNESS_DATASET_SEEDS + FITNESS_MODEL_SEEDS).isdisjoint(
        VALIDATION_DATASET_SEEDS + VALIDATION_MODEL_SEEDS
    )


def test_b1_accepts_exact_frozen_componentwise_boundary():
    c = HardConstraints()
    cutoff = m(nl=104, du=8, lat=64, degree=6, fp="cut")
    candidate = m(nl=102, du=6, lat=62, degree=6, fp="cand")
    assert in_b1_band(candidate, cutoff, c)


@pytest.mark.parametrize(
    "candidate",
    [
        m(nl=101, fp="nl-out"),
        m(du=5, fp="du-out"),
        m(lat=61, fp="lat-out"),
        m(degree=7, fp="degree-out"),
        m(sac=0.60, fp="admissibility-out"),
    ],
)
def test_b1_refuses_any_single_outside_band_component(candidate):
    c = HardConstraints()
    cutoff = m(fp="cut")
    assert not in_b1_band(candidate, cutoff, c)


def test_b1_can_cross_protected_key_only_inside_contiguous_band():
    c = HardConstraints()
    cutoff = m(nl=104, fp="cut")
    inside_better_neural = m(nl=102, fp="inside")
    outside_better_neural = m(nl=100, fp="outside")
    items = [
        ("cut", cutoff, 0.50),
        ("inside", inside_better_neural, 0.10),
        ("outside", outside_better_neural, 0.01),
    ]
    ordered = apply_phase2f_cutoff_order(
        items,
        constraints=c,
        arm="B1",
        cutoff_metrics=cutoff,
        shuffle_rng=None,
    )
    assert [x[0] for x in ordered] == ["inside", "cut", "outside"]


def test_b1_never_crosses_an_outside_band_blocker():
    c = HardConstraints()
    cutoff = m(nl=104, du=8, fp="cut")
    blocker = m(nl=103, du=4, fp="blocker")  # DU distance 4 => outside B1.
    separated_eligible = m(nl=102, du=6, fp="eligible")
    items = [
        ("cut", cutoff, 0.50),
        ("blocker", blocker, 0.40),
        ("eligible", separated_eligible, 0.01),
    ]
    ordered = apply_phase2f_cutoff_order(
        items,
        constraints=c,
        arm="B1",
        cutoff_metrics=cutoff,
        shuffle_rng=None,
    )
    assert [x[0] for x in ordered] == ["cut", "blocker", "eligible"]


def test_o0_remains_exact_protected_key_only():
    c = HardConstraints()
    cutoff = m(nl=104, fp="cut")
    same_key = m(nl=104, fp="same")
    near_other_key = m(nl=102, fp="near")
    items = [
        ("cut", cutoff, 0.50),
        ("same", same_key, 0.10),
        ("near", near_other_key, 0.01),
    ]
    ordered = apply_phase2f_cutoff_order(
        items,
        constraints=c,
        arm="O0",
        cutoff_metrics=cutoff,
        shuffle_rng=None,
    )
    assert [x[0] for x in ordered] == ["same", "cut", "near"]


def test_sb1_requires_persistent_shuffle_rng_and_is_deterministic():
    c = HardConstraints()
    cutoff = m(fp="cut")
    items = [
        ("cut", cutoff, 0.5),
        ("a", m(nl=102, fp="a"), 0.1),
        ("b", m(nl=103, fp="b"), 0.2),
    ]
    with pytest.raises(ValueError):
        apply_phase2f_cutoff_order(
            items,
            constraints=c,
            arm="SB1",
            cutoff_metrics=cutoff,
            shuffle_rng=None,
        )
    one = apply_phase2f_cutoff_order(
        items,
        constraints=c,
        arm="SB1",
        cutoff_metrics=cutoff,
        shuffle_rng=random.Random(536011),
    )
    two = apply_phase2f_cutoff_order(
        items,
        constraints=c,
        arm="SB1",
        cutoff_metrics=cutoff,
        shuffle_rng=random.Random(536011),
    )
    assert one == two


def test_phase2f_verdict_is_fail_closed_and_requires_all_seven_gates():
    assert len(SUPPORT_CHECKS) == 7
    all_green = {name: True for name in SUPPORT_CHECKS}
    assert phase2f_verdict(False, all_green) == "phase2f_inconclusive_prerequisites"
    assert phase2f_verdict(True, all_green) == "phase2f_minimal_band_pressure_supported"
    one_red = dict(all_green)
    one_red[SUPPORT_CHECKS[0]] = False
    assert phase2f_verdict(True, one_red) == "phase2f_minimal_band_pressure_not_supported"
    with pytest.raises(ValueError):
        phase2f_verdict(True, {name: True for name in SUPPORT_CHECKS[:-1]})
