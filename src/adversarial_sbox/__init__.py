"""Adversarial S-Box research package."""

from .cryptoshield import (
    algebraic_degree,
    differential_distribution_table,
    differential_uniformity,
    is_bijective,
    linear_approximation_table,
    max_linear_correlation,
    nonlinearity,
    sac_score,
    validate_sbox,
)
from .datasets import PairSample, generate_balanced_pairs, split_dataset
from .provenance import fingerprint_dataset, fingerprint_sbox
from .spn import ToySPN

__all__ = [
    "PairSample",
    "ToySPN",
    "algebraic_degree",
    "differential_distribution_table",
    "differential_uniformity",
    "fingerprint_dataset",
    "fingerprint_sbox",
    "generate_balanced_pairs",
    "is_bijective",
    "linear_approximation_table",
    "max_linear_correlation",
    "nonlinearity",
    "sac_score",
    "split_dataset",
    "validate_sbox",
]
