# Secretkeeper COSE_Encrypt0 sequence security — experimental hardening

**Status: development-only security regression; NOT Android hardware verification.**

## Audit finding

The legacy AOSP-compatible `ExternalAadMode.EMPTY` profile authenticates the
protected COSE header (algorithm + session ID) and ciphertext, but NOT the
packet's `sequence_number` metadata. Consequently:

- `decrypt(..., expected_sequence_number=n, aad_mode=EMPTY)` compares a
  potentially attacker-controlled number to the caller's expectation, but the
  AES-GCM tag cannot detect a relabelled sequence value. This does **not**
  establish anti-replay resistance.
- A replay counter alone cannot fix this problem if the counter value is not
  bound cryptographically to the packet. A ciphertext for sequence 0 may be
  relabelled as sequence 1 in the legacy EMPTY profile.

This observation is limited to the module's explicit AAD modes. Do not claim
that a particular deployed AOSP branch is vulnerable: its native transport or
session layer might supply additional anti-replay guarantees not implemented
by this development codec.

## Hardened and explicitly scoped path

`decrypt_and_consume(..., window=SequenceWindow())` now:

1. Requires the explicit `REQUEST_SEQNUM_U64` external AAD profile, which
   cryptographically binds the uint64 request sequence to the AES-GCM tag.
2. Takes the receiver's next expected number from the session-scoped window;
   it does not trust a sequence claimed by the sender as the expected number.
3. Verifies session binding and AES-GCM authenticity **before** advancing the
   window, preventing malformed messages from consuming sequence numbers.
4. Uses a lock around sequence consumption so simultaneous attempts at the
   same sequence cannot both complete.
5. Rejects non-integral, boolean, negative or over-uint64 sequence values,
   counter exhaustion, malformed IV and malformed session IDs.
6. Keeps legacy `encrypt/decrypt` APIs for AOSP compatibility and explicitly
   documents their weaker protection when `EMPTY` is selected.

## Important non-goals and remaining security gates

- The `SequenceWindow` is in-memory and **not rollback-protected**. A restart
  or hostile host could reset it; do not treat it as an anti-replay solution
  against the project’s full hostile-host threat model.
- An authenticated session must provide unique per-direction keys and avoid
  AES-GCM nonce/IV reuse under a given key. The crypto utility permits
  explicitly supplied IVs for deterministic interoperability tests but does
  **not** enforce per-key IV uniqueness or negotiate keys.
- Real native AOSP AuthGraph/SkSession negotiation must pin the applicable
  AAD profile and validate the platform's native sequence rules. Do not
  silently select EMPTY as a fallback for replay-sensitive operations.
- This does not add native Android session establishment, attestation, or
  production Secretkeeper support. Physical device/pVM hostile-host testing
  and authoritative trust provisioning remain separate unfinished gates.

### Evidence

`tests/secure_core_mobile/test_secretkeeper_sequence_hardening.py`
contains positive and negative regression tests, including an explicit
demonstration that relabelling the legacy EMPTY-mode packet passes bare
decryption but fails the authenticated-sequence path.

All changes are isolated on a branch based on
`secure-core-mobile/main`; Phase 2G/2H/2R scientific results and branches are
unchanged.
