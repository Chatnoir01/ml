# CryptoWall Hybrid HPKE Lab — X25519 + ML-KEM-768

**Status: research-only; opt-in; not production, not sender-authenticated,
not a Signal-like protocol; DO NOT deploy against real user messages.**

## Standards and library basis

- NIST **FIPS 203** (2024): ML-KEM standardized key encapsulation
  https://csrc.nist.gov/pubs/fips/203/final
- IETF **RFC 9180**: HPKE construction
  https://www.rfc-editor.org/rfc/rfc9180
- IETF **RFC 10024** (August 2026): X25519MLKEM768 hybrid key agreement
  **for TLS 1.3**. Useful standards context, but our separate experimental
  HPKE envelope **is not an RFC 10024 TLS implementation**.
  https://www.rfc-editor.org/rfc/rfc10024.html
- `cryptography` 49+ provides an explicit **hybrid HPKE KEM profile**,
  `KEM.MLKEM768_X25519` (X-Wing), `KDF.HKDF_SHA256`,
  `AEAD.AES_256_GCM`. Use these library primitives unchanged rather
  than invent an unreviewed KEM combiner. Backend must actually support
  ML-KEM; unsupported machines **FAIL**, never downgrade.
  https://cryptography.io/en/49.0.0/hazmat/primitives/hpke/

**This is intentionally separate from CryptoWall v1** X25519-only envelope.
It has a different, explicit `CWALLPQ1\0` magic; a v1 classical ciphertext
cannot be accepted as a hybrid ciphertext. There is **no implicit migration
or fallback**.

## Experiment contract

1. Generate one in-memory recipient `MLKEM768X25519PrivateKey` from
   independent ML-KEM-768 and X25519 private components (library API).
2. Encrypt messages under recipient's corresponding public key with
   `Suite(KEM.MLKEM768_X25519, KDF.HKDF_SHA256, AEAD.AES_256_GCM)`.
   The library owns hybrid secret combination and ephemeral encapsulation.
3. Bind application context to HPKE `info` using a fixed domain and explicit
   32-bit context length. A different context must fail authentication.
4. Store only binary envelope `CWALLPQ1\0 || enc || AEAD_ciphertext`.
   HPKE `enc` length is queried from KEM metadata; inputs are bounded:
   maximum plaintext 8 MiB, context 4096 bytes.
5. Tests cover correct roundtrip, repeat encryption uniqueness, wrong
   recipient, wrong context, field tampering, truncation, suffix injection,
   wrong key/format, no classical downgrade, and **replay acceptance** as
   an explicitly missing property.
6. CI on Python 3.10/3.11/3.12 must probe actual ML-KEM availability
   and run the real ML-KEM/AES-GCM tests. No simulated success; generic
   Phase 0 may skip this optional library only when `[pq]` isn't installed.

## What is still missing

- Authentication/identity binding of the **recipient public key**;
  a substituted key defeats confidentiality.
- Sender identity and anti-replay/sequence tracking.
- A reviewed key lifecycle, revocation, storage, recovery and multi-device.
- Forward secrecy against later compromise of the recipient's static
  private key. The hybrid encapsulation by itself is **not** a ratchet
  or post-compromise recovery protocol.
- Security against traffic analysis, malicious endpoints, memory
  exposure, protocol reflection, selective downgrade from an *external*
  negotiator, side channels and server compromise.
- External interoperability vectors, cryptographic audit, formal protocol
  analysis, reproducible locked dependency hashes and deployment review.

Hybrid HPKE ciphertext **does not mean a production-approved quantum-safe
messenger**. The KEM may provide post-quantum confidentiality under its
assumptions, but our application protocol and trust deployment have not
been qualified.

## Local verification (without user data)

```bash
python -m pip install -e ".[dev,crypto,pq]"
python -m pytest tests/test_cryptowall_hybrid_hpke.py
```

No private keys, test messages from actual users, or shared secrets are
committed to GitHub.
