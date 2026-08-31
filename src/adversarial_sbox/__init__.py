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
from .spn import ToySPN

__all__ = [
    "ToySPN",
    "algebraic_degree",
    "differential_distribution_table",
    "differential_uniformity",
    "is_bijective",
    "linear_approximation_table",
    "max_linear_correlation",
    "nonlinearity",
    "sac_score",
    "validate_sbox",
]
