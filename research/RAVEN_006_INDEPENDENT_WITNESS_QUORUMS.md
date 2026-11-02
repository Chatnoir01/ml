# RAVEN-006 — Independent witness attestations and quorum safety

**Status: research-only, single-transition quorum model. No deployment, formal proof, trusted hardware, consensus or production finality.**

## 1. Research objective

RAVEN-005 let an observer detect two issuer-signed checkpoint claims after receiving both through gossip. RAVEN-006 examines a *different* property: can separately administered witnesses, each with a pinned Ed25519 signing key, produce quorum certificates for mutually incompatible claims originating from the **same, pinned genesis checkpoint**, while no more than f witness keys have been compromised?

This tests a familiar Byzantine quorum-intersection principle in our experiment. **It is not a new consensus algorithm.**

### Threat model and assumptions

- A fixed immutable-in-principle roster of **n distinct independent witness public keys**, pinned out of band with issuer key, namespace, compartment and genesis commitment.
- At most **f witness keys** behave Byzantine, with \`n >= 3f + 1\`. This is an *assumption*, never provable by inspecting signatures.
- Each honest witness signs **at most one distinct checkpoint receipt per pinned parent epoch/commitment**; that guard survives *all* restarts in the intended theorem, although **the current code uses only RAM and does not provide this property**.
- Ed25519 signing keys are exclusive to the asserted witnesses and signatures are unforgeable. A stolen key counts as compromised.
- The issuer checkpoint claim has a valid signature, names the pinned domain and is an immediate child of the pinned genesis. **RAVEN-006 currently excludes later epochs.**
- No anonymous witness registration, Sybil resistance, robust key rotation, device custody, network availability guarantees, reliable time source, authenticated finality or real commitment service.
- A signature proves an endorsement by the associated key. It does **not** prove that data was durably stored, that a proposal was applied, or that any party is acting honestly.

## 2. Mathematical quorum rule

Let \`N\` be the roster of \`n\` witnesses. Configure:

- \`n >= 3f + 1\`
- \`q = n - f\` independent witness endorsements per candidate.

For two quorums Q1 and Q2 of size at least q:

\`|Q1 ∩ Q2| >= 2q - n = n - 2f > f.\`

Under the assumed fault bound, the intersection contains at least one honest signer. If all honest signers *persistently* refuse to endorse incompatible children of the same parent, **two incompatible certificates for that exact parent cannot both form.**

This is a **conditional quorum-intersection argument** for a single step, not a proof of Byzantine consensus safety or liveness across arbitrary reconfigurations and epochs.

| n | f | Required quorum q | Minimum intersection | Honest intersection lower bound |
|---:|---:|---:|---:|---:|
| 1 | 0 | 1 | 1 | 1 (not independently distributed) |
| 4 | 1 | 3 | 2 | 1 |
| 7 | 2 | 5 | 3 | 1 |
| 10 | 3 | 7 | 4 | 1 |

With fewer than \`n-f\` reachable signers, **liveness may fail**. Safety does not imply availability.

## 3. Data structures

- \`Roster\`: issuer key and scope; pinned genesis; independent witness keys; configured max Byzantine count; q=n-f.
- \`Attestation\`: Ed25519-signed, domain-separated canonical receipt hash and explicit issuer / compartment / namespace / genesis / parent / child epoch fields.
- \`HonestWitness\`: holds witness private key and the RAVEN-005 rooted receipt observer; enforces at most one distinct signed checkpoint claim per parent using an **in-memory** guard. Re-instantiation with the same key loses the guard (intentional negative control).
- \`QuorumCertificate\`: issuer-signed checkpoint claim and tuple of independently verifiable witness endorsements.
- \`verify_quorum_certificate\`: checks pinned roots, issuer signature, unique roster witnesses, every witness signature and quorum size. **It does not consult a live committed anchor.**
- \`prove_witness_double_vote\`: returns two independently verifiable conflicting attestations from the **same witness key** for different child commitments/policy digests of the same parent.

Canonical JSON is experimental: there is no cross-language canonical encoding standard, wire parser or format migration plan.

### What is *not* in the evidence

A valid QC does not prove a checkpoint is finalized on stable storage, does not prove inclusion in an append-only log, and does not demonstrate receipt publication to all clients. A fork proof provides evidence of two signed statements, not conclusive proof of criminal intent or hardware compromise.

## 4. Negative controls and falsification tests

1. Valid QC (n=1/4/7/10) passes cryptographic verification.
2. Insufficient signers cannot form a valid QC.
3. Repeating a signature does not increase independent witness count.
4. Honest witness refuses signing conflicting receipts for the same pinned parent.
5. At most one Byzantine key in n=4/f=1 cannot produce two incompatible q=3 certificates **if** all three honest guards are durable.
6. **Exceed bound:** when two out of four witness keys sign both branches, two conflicting q=3 certificates are accepted. Their double endorsements form independently verifiable evidence. This explicitly demonstrates failure outside the f=1 assumption.
7. **Rollback guard:** reinitializing the same honest witness with the same private key allows double endorsement (in-memory state is not durable). A signature cannot detect lost signing memory.
8. Forged signatures, cross-domain binding, unregistered witnesses, mutated fields and wrong issuer keys are rejected.
9. Non-genesis parent transitions are rejected by the scope gate.
10. Partitions with too few available witnesses cannot form a quorum; restoring availability enables collection of enough signatures in the test scenario.
11. Pinned roster changes invalidate prior attestations if keys change (membership governance remains unsolved).
12. Quorum validity WITHOUT a trusted committed anchor is deliberately accepted by the verifier, demonstrating that **QC is not proof of finality**.

## 5. Prior art / innovation boundary

- Byzantine quorum intersection is classical fault-tolerant distributed systems theory; RAVEN-006 is an implementation of the principle, not its invention.
- **RFC 9162 Certificate Transparency v2** provides signed checkpoints and append-only Merkle consistency/inclusion proofs: https://www.rfc-editor.org/rfc/rfc9162.html
- **RFC 9420 Messaging Layer Security** provides authenticated group epochs, commitments and key schedules: https://www.rfc-editor.org/rfc/rfc9420.html

A future claimed contribution must prove a new composition property or measurable improvement over appropriate baselines, while documenting the failure model and operational cost.

## 6. Known gaps and next experiment

| Gap | Concrete next action |
|---|---|
| Honest witness rollback can violate safety assumption | Implement experimental crash-durable witness vote journal; inject process termination and disk restoration |
| Quorum signature can be produced without a committed checkpoint | Bind to a verifiable finality/commit certificate under a separately justified model |
| Signatures from witness identities do not establish independent administration | Define independent custody, attestation and anti-Sybil governance assumptions |
| Later epochs and roster changes not covered | Model reconfiguration with cross-epoch quorum overlap and explicitly signed membership changes |
| Byzantine withholding and partitions can block progress | Model adversarial schedules, fairness and quorum availability; measure availability vs safety |
| Network overhead and witness-signing cost not measured | Benchmark CPU, latency, memory, bandwidth and state growth with reproducible versions |
| No state-space proof | Add bounded exhaustive schedule enumeration or model checking with explicit invariants |

**RAVEN-007 proposal:** durable one-vote-per-parent protection and explicit cross-epoch reconfiguration safety. A full Byzantine consensus system should not be improvised before comparing to existing, independently reviewed protocols.
