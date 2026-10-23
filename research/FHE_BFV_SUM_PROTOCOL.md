# Homomorphic computation lab — BFV encrypted sum

**Status:** real library *demonstration*, not a production FHE cloud service.
The project is isolated from real medical, financial or private records.

## Actual mechanism

Use [TenSEAL](https://github.com/OpenMined/TenSEAL), built on Microsoft SEAL,
to demonstrate additively homomorphic arithmetic using BFV.

- **Owner/client** generates an in-memory BFV encryption context with
  `poly_modulus_degree=8192` and `plain_modulus=1032193`.
- Input values are at most eight **synthetic nonnegative integers** each
  between 0 and 1000. The maximum true sum is bounded below modulus
  wraparound; negative/oversized/noninteger inputs are rejected.
- Owner encrypts each value into a BFVVector and serializes each ciphertext.
- A *copy* of the owner context is made public with
  `make_context_public()`. Before sharing and after deserialization we
  verify `has_secret_key() == False` and `is_public() == True`.
  The raw private context is never written or sent to a remote evaluator.
- The **cloud** receives only serialized public context and ciphertext bytes,
  deserializes BFV vectors and adds them while encrypted. A private context
  is explicitly refused. It emits **another ciphertext**, not plaintext.
- The **owner** decrypts the returned ciphertext using the original local
  private context, compares the exact result with the known cleartext
  reference and checks the public key access boundary.

This validates **one exact arithmetic operation** on real FHE ciphertexts.
It does not exercise arbitrary deep circuits, bootstrapping, privacy against
traffic analysis, unauthorized decryption on a compromised owner device,
secure key persistence, protocol authentication, cloud isolation or
side-channel resistance.

## Performance and security caveats

- BFV computation is exact modulo the chosen plaintext modulus. The bounded
  test avoids wraparound; this is *not* an unrestricted medical analytics API.
- Real security strength depends on parameters, ciphertext modulus and
  library configuration. This demonstration does **not** claim a measured
  NIST security level or production parameter approval.
- The cloud has no **secret key**, but learns the public context, number and
  sizes of ciphertexts, operation type and timing.
- Only the owner can decrypt *under the intended model*. Owner malware,
  accidental secret serialization or key theft are not in scope.
- TenSEAL 0.3.18 currently supplies Python 3.11 and 3.12 wheels; the
  dedicated CI tests those two versions. Legacy Phase 0 on 3.10 skips only
  this optional-dependency test module, not existing Phase 0 tests.
- Later expand to noise budget, serialization size, latency, ciphertext
  rotation and security-parameter review **before** evaluating CKKS or
  processing regulated personal data.

## Reproduce on synthetic numbers

```bash
python -m pip install -e ".[dev,fhe]"
python -m pytest tests/test_fhe_lab.py
```

References: [TenSEAL](https://github.com/OpenMined/TenSEAL),
[OpenFHE](https://github.com/openfheorg/openfhe-python).
