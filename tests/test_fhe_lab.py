"""Real TenSEAL BFV encryption, no fake arithmetic; research demo only."""

from __future__ import annotations

import pytest

# Legacy Phase 0 deliberately has no TenSEAL dependency.
# The separate CI installs it and explicitly refuses skipped tests.
pytest.importorskip("tenseal")

from fhe_lab.aggregate import (
    cloud_encrypted_sum,
    decrypt_sum,
    demonstration,
    encrypt_inputs,
)


@pytest.mark.parametrize("values", [
    (1,), (1, 2, 3), (0, 0, 0), (1000, 1000, 1000, 1000),
])
def test_true_encrypted_sum_recovers_exact_integer(values):
    result = demonstration(values)
    assert result["scheme"] == "BFV_demo_exact_addition"
    assert result["encrypted_sum"] == sum(values)
    assert result["correct"] is True
    assert result["server_received_secret_key"] is False
    assert result["production_security_claim"] is False


def test_public_cloud_context_has_no_private_key():
    private, public_bytes, ciphertexts = encrypt_inputs([2, 3])
    import tenseal as ts
    public = ts.context_from(public_bytes, n_threads=1)
    assert private.has_secret_key()
    assert not public.has_secret_key()
    with pytest.raises(Exception):
        public.secret_key()
    encrypted_answer = cloud_encrypted_sum(public_bytes, ciphertexts)
    assert decrypt_sum(private, encrypted_answer) == 5


def test_cloud_refuses_secret_context_even_when_serialized():
    private, _, ciphertexts = encrypt_inputs([1, 2])
    secret_bytes = private.serialize(save_secret_key=True)
    with pytest.raises(ValueError, match="refuses a private context"):
        cloud_encrypted_sum(secret_bytes, ciphertexts)


@pytest.mark.parametrize("values", [
    [], list(range(9)), [2, -1], [True, 4], [2.5], ["3"], [1001], [None]
])
def test_invalid_plaintext_inputs_rejected(values):
    with pytest.raises((TypeError, ValueError)):
        encrypt_inputs(values)


def test_invalid_ciphertext_and_public_context_rejected():
    private, public, ciphertexts = encrypt_inputs([6, 7])
    with pytest.raises((TypeError, ValueError)):
        cloud_encrypted_sum(public, [])
    with pytest.raises((TypeError, ValueError)):
        cloud_encrypted_sum(public, [b""])
    with pytest.raises(TypeError):
        cloud_encrypted_sum("not bytes", ciphertexts)
    with pytest.raises((TypeError, ValueError)):
        decrypt_sum(private, b"")


def test_cloud_has_no_decryption_access_without_private_context():
    private, public_bytes, ciphertexts = encrypt_inputs([8, 9])
    encrypted_answer = cloud_encrypted_sum(public_bytes, ciphertexts)
    import tenseal as ts
    public = ts.context_from(public_bytes, n_threads=1)
    with pytest.raises(ValueError, match="requires owner private"):
        decrypt_sum(public, encrypted_answer)
    assert decrypt_sum(private, encrypted_answer) == 17
