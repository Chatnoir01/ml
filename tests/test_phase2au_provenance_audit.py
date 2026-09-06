"""RED regression for the Phase 2A-U incomplete prior-neural-seed registry."""

from adversarial_sbox.phase2ap import DATASET_SEEDS as P2AP_DATASET_SEEDS
from adversarial_sbox.phase2ap import MODEL_SEEDS as P2AP_MODEL_SEEDS
from adversarial_sbox.phase2au import fresh_seed_registry, fresh_seeds_disjoint_from_prior


def test_historical_phase2au_freshness_detects_prior_phase2ap_overlap():
    prior_phase2ap = set(P2AP_DATASET_SEEDS) | set(P2AP_MODEL_SEEDS)
    overlap = set(fresh_seed_registry()) & prior_phase2ap

    assert overlap == {
        74003,
        74017,
        74027,
        74047,
        74071,
        74093,
        74101,
        84011,
        84017,
        84029,
        84061,
        84067,
        84089,
    }
    # This assertion is intentionally RED against the historical implementation:
    # a complete prior registry must reject Phase 2A-U as fresh.
    assert fresh_seeds_disjoint_from_prior() is False
