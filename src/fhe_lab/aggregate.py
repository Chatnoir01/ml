"""Research-only exact encrypted sums with TenSEAL BFV.

The server receives *only* a public context and ciphertexts; decryption
occurs only on the client. Toy bounded numbers, no real/private user data.
Not independently audited; no production FHE security parameters claimed.
"""

from __future__ import annotations

from collections.abc import Sequence

PLAIN_MODULUS = 1032193
POLY_MODULUS_DEGREE = 8192
MAX_ITEMS = 8
MAX_VALUE = 1000


def _tenseal():
    try:
        import tenseal as ts
    except ImportError as exc:
        raise RuntimeError("TenSEAL required: install optional [fhe] extra") from exc
    return ts


def _validated_values(values: Sequence[int]) -> tuple[int, ...]:
    if not isinstance(values, (tuple, list)):
        raise TypeError("values must be a list or tuple of integers")
    if not (1 <= len(values) <= MAX_ITEMS):
        raise ValueError("number of encrypted values is outside demo limits")
    if any(type(x) is not int or not (0 <= x <= MAX_VALUE) for x in values):
        raise ValueError("demo inputs must be nonnegative bounded integers")
    return tuple(values)


def encrypt_inputs(values: Sequence[int]):
    """Local owner step: returns PRIVATE context, PUBLIC bytes, encrypted bytes.

    The private context MUST never be uploaded to an external/cloud service.
    """
    ts = _tenseal()
    numbers = _validated_values(values)
    private = ts.context(
        ts.SCHEME_TYPE.BFV,
        poly_modulus_degree=POLY_MODULUS_DEGREE,
        plain_modulus=PLAIN_MODULUS,
        n_threads=1,
    )
    if not private.has_secret_key():
        raise RuntimeError("BFV context unexpectedly lacks owner secret key")
    ciphertexts = tuple(
        ts.bfv_vector(private, [value]).serialize() for value in numbers
    )
    public = private.copy()
    public.make_context_public()
    if public.has_secret_key() or not public.is_public():
        raise RuntimeError("public context still contains a secret key")
    public_serialized = public.serialize(save_secret_key=False)
    # Double-check the exact representation delivered to cloud consumers.
    receiver_context = ts.context_from(public_serialized, n_threads=1)
    if receiver_context.has_secret_key() or not receiver_context.is_public():
        raise RuntimeError("serialized public context leaks secret key")
    return private, public_serialized, ciphertexts


def cloud_encrypted_sum(public_context: bytes, ciphertexts: Sequence[bytes]) -> bytes:
    """Compute encrypted sum WITHOUT owner secret: no plaintext handling here."""
    ts = _tenseal()
    if not isinstance(public_context, bytes):
        raise TypeError("server context must be serialized public bytes")
    if not isinstance(ciphertexts, (tuple, list)) or not 1 <= len(ciphertexts) <= MAX_ITEMS:
        raise ValueError("server input ciphertext count invalid")
    if any(not isinstance(value, bytes) or not value for value in ciphertexts):
        raise ValueError("server requires nonempty ciphertext bytes")
    public = ts.context_from(public_context, n_threads=1)
    if public.has_secret_key() or not public.is_public():
        raise ValueError("server refuses a private context")
    result = None
    for ciphertext in ciphertexts:
        item = ts.bfv_vector_from(public, ciphertext)
        result = item if result is None else (result + item)
    assert result is not None
    return result.serialize()


def decrypt_sum(private_context, encrypted_sum: bytes) -> int:
    """Only the client-side owner can decrypt. No raw secret-key export."""
    ts = _tenseal()
    if not hasattr(private_context, "has_secret_key") or not private_context.has_secret_key():
        raise ValueError("client decryption requires owner private context")
    if not isinstance(encrypted_sum, bytes) or not encrypted_sum:
        raise TypeError("result ciphertext must be bytes")
    result = ts.bfv_vector_from(private_context, encrypted_sum).decrypt()
    if len(result) != 1 or type(result[0]) is not int:
        raise ValueError("unexpected BFV result shape")
    if not (0 <= result[0] <= MAX_ITEMS * MAX_VALUE):
        raise ValueError("BFV result outside demo range or invalid parameters")
    return result[0]


def demonstration(values: Sequence[int]) -> dict[str, int | bool | str]:
    """Full client→cloud→client workflow, synthetic integers only."""
    numbers = _validated_values(values)
    secret, public_bytes, encrypted = encrypt_inputs(numbers)
    result = cloud_encrypted_sum(public_bytes, encrypted)
    recovered = decrypt_sum(secret, result)
    return {
        "scheme": "BFV_demo_exact_addition",
        "count": len(numbers),
        "encrypted_sum": recovered,
        "correct": recovered == sum(numbers),
        "server_received_secret_key": False,
        "production_security_claim": False,
    }
