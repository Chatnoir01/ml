# CryptoWall v1 — experimental public-key encryption envelope

**Status: software prototype, not independently audited, not a secure messenger.**
The module is intentionally isolated from the experimental S-Box research in
`adversarial_sbox`; none of our neural/evolutionary S-Boxes are used for
real-world encryption.

## Scope and actual security construction

- One-way, offline encryption to a *pinned* recipient X25519 public key.
- Sender creates a **fresh ephemeral X25519 keypair** for each envelope.
- X25519 ECDH -> HKDF-SHA-256 (32-byte AEAD key), with 16-byte random salt,
  version-domain separation and binding to both public keys.
- AES-256-GCM authenticates and encrypts the plaintext; includes an untruncated
  128-bit authentication tag. Fresh random 96-bit nonce per envelope.
- The complete versioned binary header and caller-supplied context are
  authenticated as associated data (AAD).
- Defined envelope format (bytes):
  `"CWALLv1\\0" (8) || recipient_id (16) || ephemeral_pub (32) || salt (16) || nonce (12) || ciphertext_and_tag (>=16)`.
- The 16-byte recipient ID is a routing fingerprint:
  SHA-256(`"CryptoWall-v1-recipient:" || recipient_public`)[:16].
  It is NOT a proof of the recipient's identity.
- AAD = `header || uint32_be(context_length) || context`. Context itself
  must be provided unchanged during decryption; it is not in the envelope.
- Maximum plaintext = 8 MiB. Maximum context = 4096 bytes. Larger payloads
  must be handled with a properly specified streaming construction; do not
  simply chunk GCM messages while reusing a nonce.
- No raw private key is written by this module. Public-key fingerprints can
  be displayed to humans; verification must occur over an authenticated
  channel, not the same untrusted channel as the untrusted key.

The construction uses the well-established `cryptography` Python library,
rather than inventing a new cipher. These are *implementation design
properties*, not a third-party security assessment.

## Threat model and explicitly unachieved properties

| Threat | Result in this prototype |
| --- | --- |
| Passive interceptor of envelope | Intended confidentiality under X25519/AES-256-GCM assumptions, with an authentic recipient key |
| Altered ciphertext/header/context | Authenticated-decryption failure |
| Envelope encrypted to wrong recipient | Reject by recipient ID and/or AEAD |
| Recipient-key substitution before encryption | **NOT prevented**; callers must authenticate key distribution |
| Sender impersonation | **NOT prevented**; anyone can encrypt to a public key |
| Replayed valid envelope | **NOT prevented**; caller needs durable anti-replay state |
| Compromise of long-term recipient private key | Old recorded envelopes become decryptable; **NO forward secrecy against recipient-key compromise** |
| Compromised sender/recipient device | No protection against local malware reading plaintext or keys |
| Quantum-capable attacker | X25519 provides no post-quantum key establishment; **NOT PQ-resistant** |
| File/message metadata confidentiality | Packet lengths, recipient routing ID, timing are visible |
| Side-channel, memory zeroization or secure key storage | Not established by Python or this module |

**Do not claim** an independently audited messenger, end-to-end authenticated
chat, sealed sender, Signal-style Double Ratchet, post-quantum protection,
strong endpoint compromise resistance, or a full high-assurance encryption wall.

## Key-management boundaries

`generate_recipient()` returns an in-memory X25519 private-key object and
public-key bytes. There is deliberately **no key persistence or export
facility** in the proof of concept. Production key creation, backup, recovery,
revocation, trust-on-first-use policy, transparency/verification, secret-key
storage, rotation and multi-device enrollment require a separately reviewed
protocol and implementation.

Do not add passwords to version control, print raw keys, upload user secrets
or decrypt/store production customer conversations with this test tool.

## Engineering acceptance / next gates

1. Review library versions and independent test vectors; add property-based
   mutation/fuzz tests, dependency scanning, memory and side-channel review.
2. Pin dependency hashes and reproducible build provenance. This PR's
   `cryptography>=43.0` is a compatibility floor, not a supply-chain lock.
3. Verify external peer identities; design stable sender authentication,
   replay resistance, revocation, device onboarding and authenticated
   transcript binding using a reviewed **established** protocol.
4. For **messaging**, evaluate a vetted Signal-like protocol or MLS
   implementation instead of expanding this file into a bespoke protocol.
5. For post-quantum transition, consider a vetted standardized ML-KEM-based
   **hybrid key-establishment** design with robust downgrade protections;
   do not simply concatenate unverified crypto outputs or claim PQ security.
6. Commission an independent audit, perform adversarial integration tests,
   and build hardware/operational verification before any production claim.

## Quick local proof (not a production deployment)

Install: `python -m pip install -e ".[dev,crypto]"`

```python
from cryptowall import generate_recipient, seal, open_envelope

my_private, my_public = generate_recipient()
ciphertext = seal(my_public, b"private demo", context=b"demo:v1")
assert open_envelope(my_private, ciphertext, context=b"demo:v1") == b"private demo"
```

Run: `python -m pytest -q tests/test_crypto_wall.py`

**Important:** Copying a raw public key from a malicious website does not
provide authenticated end-to-end encryption. Check the fingerprint through
an independently trusted channel.
