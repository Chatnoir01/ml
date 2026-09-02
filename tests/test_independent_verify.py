import pytest

from adversarial_sbox.independent_verify import verify_independently
from adversarial_sbox.references import AES_SBOX


def test_independent_verifier_reproduces_aes_reference_metrics():
    metrics = verify_independently(AES_SBOX)
    assert metrics.nonlinearity == 112
    assert metrics.differential_uniformity == 4
    assert metrics.max_linear_correlation == 32
    assert metrics.algebraic_degree == 7
    assert abs(metrics.sac_score - 0.5048828125) < 1e-15


def test_independent_verifier_rejects_non_permutation():
    with pytest.raises(ValueError, match="permutation"):
        verify_independently(tuple([0] * 256))
