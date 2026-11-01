# RAVEN-005 — Witness gossip / verifiable equivocation research protocol

Status: **experimental, not a secure distributed service and not an established cryptographic innovation**.

## Goal and falsifiable claim

Given two distinct *issuer-signed checkpoint claims* from the same trusted genesis parent, independent clients should be able to produce publicly checkable evidence of inconsistent signed statements once a gossip path delivers **both** claims to one honest witness.

Hypothesis H-005: with authenticated, correctly scoped checkpoint receipts, correctly provisioned issuer key and genesis commitment, and a connected gossip exchange that eventually transmits every outstanding receipt, every honest witness will eventually detect an existing directly conflicting signed sibling pair. This is a conditional algorithmic property, NOT a latency guarantee in asynchronous networks.

A *separately administered independent server*, real persistent publication, or real consensus protocol is **not** present in the simulation.

## Components

- \`research/raven_fork_evidence.py\` (RAVEN-004): authenticated signed-checkpoint claims and portable conflicting-claim pair.
- \`research/raven_witness_model.py\`: signed receipt admission, strict issuer/namespace/compartment checks, a pinned genesis commitment and issuer public key, orphan receipt storage, rooted ancestry reconstruction, bounded memory, deterministic gossip and synthetic directed network partitions.
- \`tests/test_raven_witness_model.py\`: adversarial positive and negative controls (including parametrized 4/8/16-witness topologies and a same-round propagation regression).

### Important semantics

1. Each witness verifies an Ed25519 receipt **directly against its own pinned issuer key**; another witness's assertion of validity is not accepted as authority.
2. Receipts whose parents are unknown are stored as **orphans**; they do not contribute fork evidence until their ancestry connects to the pinned genesis.
3. Two rooted, independently signed receipts are contradictory if they identify the same issuer, compartment, namespace, parent epoch/commitment and child epoch but commit to differing child commitment or policy digest.
4. A bounded witness returns at most one verifiable conflicting pair per parent; this prevents quadratic proof-list growth but does not establish Byzantine DoS resilience.
5. A gossip message transfers full signed receipts; there is **no quorum certificate**, witness attestation, encrypted transport or endorsement.
6. Network rounds take a snapshot of each sender's receipts at the start. A receipt arriving in a given round cannot be forwarded again in that same round. Earlier code lacked this rule and yielded unrealistically fast multi-hop propagation; a dedicated regression test catches it.
7. The "bytes sent" metric counts application-level signed receipt body + signature only; it excludes transport headers, TLS, retries, serialization framing and network overhead.

## Attack simulations

| ID | Attack or condition | Expected classification |
|---|---|---|
| W01 | Conflicting issuer-signed rooted child states at two isolated witnesses | Not detected until both become visible to a common verifier |
| W02 | Partition heals, witness receives both certificates | Evidence becomes verifiable |
| W03 | Permanent selective withholding of one certificate | Undetectable within the model; **not** evidence of consistency |
| W04 | Recipient receives child before parent | Orphan retained, not treated as an anchored history |
| W05 | Forged signature or mutated signed field | Reject |
| W06 | Properly signed receipt for different namespace/compartment | Reject under pinned scope |
| W07 | Receipt from unpinned root or issuer key | Reject gossip or remain unanchored |
| W08 | Duplicate receipt or retransmission | Idempotent |
| W09 | Receipt capacity exhausted | Fail closed; availability can be lost |
| W10 | Directed partition or unidirectional link | No unfounded detection or liveness claim |
| W11 | Connected 4, 8 and 16 witness rings | Expected eventual detection in the deterministic model |
| W12 | New data relayed by intermediate witness during same round | Prohibited by snapshot-based round semantics |

## Local reproduction and measurements

Local research run executed using Python 3.13.5, pytest 9.0.2, cryptography 46.0.4 and a local compatibility copy of the RAVEN-004 receipt interface. **23 parametrized test instances passed**. The full GitHub repository and its new GitHub Actions jobs must be tested separately; the compatibility copy does not count as a full integration verification.

Deterministic, bidirectional ring; two contradictory root children issued under the same authority key to opposite positions; each edge exchanges all missing receipts once per round, using beginning-of-round snapshots:

| Witnesses | Rounds until all have evidence | Receipt transmissions | Payload + signature bytes |
|---:|---:|---:|---:|
| 4 | 2 | 6 | 2,748 |
| 8 | 4 | 14 | 6,412 |
| 16 | 8 | 30 | 13,740 |
| 32 | 16 | 62 | 28,396 |

These are **deterministic simulator observations**, not network performance forecasts. The round count tracks the topology's hop distance, not elapsed wall time. No claim is made for malicious witnesses that withhold, delay or selectively gossip. If the two claims never meet, detection is impossible.

## Strong limitations / research gaps

- **Signer authenticity and trust root distribution** are assumed preconfigured. Key rotation, revocation, compromise and split-trust issuers are unsolved.
- **Receipt finality** is not proven. The signed claim may describe an uncommitted or simulated state. See RAVEN-004 limitations.
- **No anti-equivocation prevention**, only conditional detectability.
- **No strong accountability without publication:** witnesses do not sign their observations. A client cannot prove which witness received which checkpoint when.
- **Not consensus or a transparency log:** no authenticated inclusion/consistency proofs over an append-only Merkle tree, durable storage, quorum agreement, realistic network partitions, scheduling fairness or Byzantine fault-tolerance theorem.
- **Fork evidence must be received:** no detection if all honest witnesses are isolated from one branch.
- **DoS:** stored signed receipt count is bounded, but signing/verification costs, gossip scheduling, input admission, and effective capacity exhaustion may still be exploited; simulation only.
- **No confidentiality or post-compromise recovery.**
- **Novelty:** Certificate Transparency RFC 9162 already develops append-only proofs, signed tree heads and related split-view issues. MLS RFC 9420 already defines group epochs and sequencing. A signed receipt gossip model does not establish a new cryptographic primitive or new security guarantee.

## Future research gate: RAVEN-006

Build a model with **explicit witness endorsements** and a bounded signer-fault assumption, e.g. n independent witnesses and at most f Byzantine witnesses. Before implementing quorum rules, formalize exactly what the threshold means and whether it guarantees only *fork awareness* (not canonical choice or finality). Compare against established CT gossip, key-transparency, and secure-messaging state-continuity mechanisms. Test malicious withholding, witness collusion, partitions, and authority-key rotation.

**Never deploy any RAVEN-001–005 research model as a security boundary.**
