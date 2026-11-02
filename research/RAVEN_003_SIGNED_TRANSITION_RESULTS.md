# RAVEN-003 — Signed-transition experimental results

Status: **research-only, not a production protocol, not a security proof**.

## Change under test

RAVEN-002 used a trusted set of string authorization tokens, which did not cryptographically bind transition fields. RAVEN-003 is a separate experimental model using Ed25519 signatures over deterministic canonical JSON. Its signed message binds:

- protocol domain, namespace, compartment;
- previous/new epoch and previous commitment;
- current policy digest, new policy contents and digest;
- selected algorithm-suite label and event identifier.

Policy and transition commitments use SHA-256 with domain separation. The trusted *in-memory* anchor records epoch, transition commitment **and policy digest**. Suite tiers are policy configuration values **not** validated assertions of cryptographic strength.

## Testing actually executed (local)

- Command: \`pytest tests/test_raven_model.py tests/test_raven_signed_model.py\`
- Environment: CPython 3.13.5, pytest 9.0.2, cryptography 46.0.4
- Result: **33 passed** (13 RAVEN-002 parameterized tests + 20 RAVEN-003 parameterized tests).
- This is a local reproduction of the research files, **not** an independent cryptographic audit.

A negative-control regression was found while testing: the first RAVEN-003 anchor recorded only epoch and transition commitment, so locally tampered policy metadata with unchanged commitment could pass checkpoint validation. This was corrected to anchor the policy digest too; the tampering test now passes.

The older general Phase 0 CI initially failed on \`ModuleNotFoundError: cryptography\` because it installed only \`.[dev]\`. The research branch was updated to add \`cryptography>=43.0\` to dev dependencies. This document does **not** claim the rerun passed; check GitHub Actions for authoritative CI status.

## Tested examples

1. Valid signed transition accepted, repeated transition rejected.
2. Mutation of namespace, compartment, epoch, commitment, policy digest, suite, event ID, policy content or signature rejected.
3. Signature from an unrelated authority rejected.
4. Authority-signed lowering of policy floor rejected.
5. Selection below the active floor rejected.
6. Stale restored snapshots rejected when the independent anchor retains newer state.
7. Two compartments evolve without sharing epoch counters; cross-target signature rejected.
8. Losing/restoring the anchor alongside state defeats rollback detection (**expected negative control**).
9. Ten sequential authorized updates accepted, later replay of old snapshots rejected.
10. Deterministic small mutation matrix rejected invalid transitions without changing trusted state.

## Important unresolved security questions

- **Authority compromise:** if signing authority compromised, it can authorize changes subject to locally enforced limits. Real trust-root provisioning/rotation/revocation is absent.
- **Crash consistency:** anchor update and local state update are not transactional. A crash between them can strand local state. Production requires an atomic or recoverable protocol.
- **Trusted anchor:** \`InMemoryAnchor\` has no actual resistance to disk rollback, memory tampering, reboot or a split-view adversary.
- **Authorization replay:** event IDs are signed but there is no independent durable global replay store. Epoch/commitment matching restricts direct replay in this single-process model.
- **Canonical encoding:** JSON serialization is defined for internal constructed Python objects only. No validated cross-language wire format or parser exists.
- **Concurrent actors:** no locking, compare-and-swap durability or multi-device consensus.
- **Data confidentiality:** no data encryption, key exchange, key erasure, forward secrecy or post-compromise recovery implemented here.
- **Novelty:** no improvement over an established cryptographic ratchet or policy-control design has been demonstrated.
- **Deployment:** do not use either RAVEN research model to secure production data.

## Next falsifiable research gate

Before implementing encrypted messages, design adversarial tests for (a) crash points at each transition step, (b) authority key rotation and stolen keys, and (c) durable anti-rollback mechanisms with fail-closed recovery. Then compare the resulting state machine to established ratchet implementations and state-continuity protocols.
