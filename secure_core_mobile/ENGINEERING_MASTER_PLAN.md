# Secure Core Mobile — Engineering Master Plan v1

Status: EXPERIMENTAL / NO HIGH-ASSURANCE CLAIM

## Mission

Test whether authorization to use cryptographic secrets can be enforced from a
trust boundary stronger than the ordinary Android application/host environment,
such that compromise of that host is not by itself sufficient to trigger
specified forbidden cryptographic operations.

No implementation milestone is evidence that this hypothesis is true.

## Non-negotiable engineering rules

1. Security claims progress independently from implementation progress.
2. Every boundary is explicitly TRUSTED, UNTRUSTED, SIMULATED,
   HARDWARE-BACKED, or TEST-EVIDENCED.
3. Fail closed on unknown capability, stale state, replay, rollback, malformed
   evidence, or policy ambiguity.
4. Secrets never enter logs, receipts, test fixtures, crash reports, or source.
5. Deterministic receipts bind build, policy, state transition, operation and
   result metadata without recording secret material.
6. Android host/app is considered adversarial in hostile-host tests.
7. No SIMULATED component may be described as hardware-backed.
8. A green unit test cannot promote a claim to ADVERSARIALLY_TESTED.
9. Cross-project imports from adversarial_sbox / GA↔NN are forbidden.
10. Reproducible tests and negative tests are first-class deliverables.

## Claim maturity

CLAIMED -> IMPLEMENTED -> TESTED -> ADVERSARIALLY_TESTED -> EXTERNALLY_VALIDATED

Promotion requires evidence. No automatic promotion from code completion.

## Workstreams

### S0 — Trust contract and threat model
Deliver:
- assets and secrets inventory;
- trust-boundary diagram;
- attacker capabilities;
- forbidden-operation catalogue;
- invariants and explicit non-goals;
- claim registry.

Gate S0: every later module maps to at least one invariant and one trust zone.

### S1 — Authorization kernel
Deliver:
- typed policy model;
- deterministic policy evaluator;
- explicit state machine;
- deny-by-default transition table;
- operation authorization transcript;
- unit/property tests.

Gate S1: forbidden transitions cannot produce authorization.

### S2 — Key lifecycle
Deliver:
- key identities/handles, never raw-key API by default;
- create/use/rotate/revoke/destroy states;
- encrypted-at-rest development backend;
- crypto-provider abstraction;
- zeroization/best-effort memory hygiene documentation.

Gate S2: policy/state denial occurs before provider operation.

### S3 — Android hardware capability layer
Deliver:
- Keystore backend;
- StrongBox capability detection;
- hardware-backed vs fallback evidence;
- fail-closed policy when hardware is required;
- device capability receipt.

Gate S3: system never labels fallback as StrongBox/hardware-backed.

### S4 — Freshness, attestation and rollback resistance
Deliver:
- nonce/challenge protocol;
- anti-replay store;
- monotonic authorization counters where platform permits;
- attestation verification boundary;
- rollback/freshness negative tests.

Gate S4: replayed/stale authorization evidence is rejected.

### S5 — Hostile-host experiment
Deliver:
- explicit compromised-host adversary harness;
- AVF/pKVM/pVM research backend where supported;
- attack scenarios targeting policy bypass and secret-use requests;
- proof receipts for rejected and successful operations;
- unsupported-device outcome rather than simulated success.

Gate S5: only this stream may begin evidence toward the central hostile-host claim.

### S6 — Messaging cryptography
Deliver:
- OpenPGP compatibility layer isolated from modern messaging;
- modern message/session layer with separate key semantics;
- no protocol conflation;
- known-answer/interoperability tests.

### S7 — Recovery, revocation, transparency
Deliver:
- recovery policy;
- revocation propagation;
- device/key replacement;
- append-only transparency receipts;
- rollback/recovery abuse tests.

### S8 — Assurance pipeline
Deliver:
- property tests;
- fuzz targets;
- dependency/SBOM generation;
- static checks;
- reproducible CI receipts;
- secret scanning;
- red-team playbooks.

### S9 — Android integration
Deliver:
- usable experimental application;
- explicit trust/capability status UI;
- operation approval/denial UI;
- receipt export without secrets;
- no security theatre: unsupported states shown honestly.

### S10 — Validation
Deliver:
- device matrix;
- adversarial regression corpus;
- independent reproduction instructions;
- external audit package when mature;
- claim registry promoted only from evidence.

## Parallel execution lanes

Lane A: S0 + claim registry + invariants.
Lane B: S1 authorization kernel.
Lane C: S2 provider/key lifecycle interfaces.
Lane D: test harness + receipts + CI.
Lane E: Android capability research and fixtures.
Lane F: hostile-host experiment design.

A-D may progress immediately. E-F may prepare interfaces/tests but cannot claim
hardware evidence without supported physical/runtime evidence.

## First executable milestone

M1 is not "secure phone". M1 is:
- executable policy engine;
- executable state machine;
- development crypto provider;
- authorization receipts;
- negative tests proving forbidden transitions are denied;
- explicit EXPERIMENTAL status.

## Repository isolation

This branch starts from repository main. Secure Core Mobile code lives under
secure_core_mobile/ and tests under tests/secure_core_mobile/. It must not import
the GA↔NN research implementation. Its CI/evidence namespace is independent.

## Definition of done

The project is never globally "done" because code exists. Each claim has its own
evidence state. High-assurance language is permitted only for the exact
properties, devices, builds and adversary model actually validated.
