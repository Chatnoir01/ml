# RAVEN-004 — Signed fork evidence and state-of-the-art boundary

**Status: experimental, in-memory, no distributed trust guarantees.**

## Objective

Let a verifier receiving two *checkpoint receipts* detect that one named
checkpoint authority signed incompatible child commitments for the same parent
namespace / compartment / epoch / parent commitment.

This is a proof of **contradictory signed checkpoint claims**, NOT a proof of
malicious intent, an objectively canonical history, a committed transaction on
physical durable storage, or a fully prevented split-view attack.

## Certificate

Receipt body, signed by Ed25519 using a dedicated checkpoint-authority key:

- Protocol domain: \`RAVEN-004/checkpoint-receipt/v1\`
- Named issuer; namespace; compartment
- Parent epoch and commitment
- Child epoch and commitment
- Child policy digest

To issue a receipt, the research authority first validates the RAVEN-003
transition signature and checks whether the assumed anchor's *current state*
matches the resulting child state.

**Known gap:** the issuer cannot prove the parent was historically anchored:
the signed transition's previous commitment is an assertion authenticated
by the transition authority. A complete design requires independently
verifiable history/consistency proofs, or a truly trusted anchor history.

## Fork-verification game

Given two receipts and the authority's independently authenticated public key:

1. Verify both Ed25519 signatures over canonical, domain-separated messages.
2. Verify that both receipts name identical issuer, namespace, compartment,
   parent epoch, parent commitment and child epoch.
3. Compare child commitment/policy digest. If different, return the two
   signed receipts as evidence of inconsistent claims.
4. Reject a missing/invalid signature, different parent or identical child.

**Key authenticity is assumed**, not implemented. No witness publication
or gossip protocol exists. Without *both* receipts a client cannot detect
a hidden fork. Splitting the checkpoint-signing authority key itself may
change what is provable and must be modeled explicitly.

## Negative and positive controls

- One shared anchor: the second device cannot advance an already changed epoch.
- Two independent anchors: both may commit different transitions.
- Two separately signed certificates for those branches: a witness that
  receives both can verify evidence of contradictory signed claims.
- A single certificate alone offers no fork detection.
- Certificate tampering and receipts signed under another key are rejected.
- A valid certificate from a different parent is not proof of a sibling fork.

## Strict prior-art comparison

- **IETF MLS RFC 9420**, particularly §§3.1, 8 and 14, already specifies
  group epochs, authenticated state, hash transcripts and handling concurrent
  Commits: https://www.rfc-editor.org/rfc/rfc9420.html
- **Certificate Transparency v2, RFC 9162** already specifies append-only
  Merkle logs, inclusion/consistency proofs, signed heads, and the challenge
  of split views / gossip: https://www.rfc-editor.org/rfc/rfc9162.html

Combining a chain hash with a signature or detecting two conflicting signed
claims is **not in itself a novel cryptographic primitive**.

A possible research contribution would have to demonstrate (and separately
verify) a *new* compositional property or material efficiency/operability
improvement relative to these mature references under identical assumptions.

## Current files

- \`research/raven_recovery_model.py\`: volatile staged/anchored/applied/cleared state machine.
- \`research/raven_fork_evidence.py\`: signed checkpoint-claim certificates and validation.
- \`tests/test_raven_recovery_model.py\`: crash, missing journal, snapshot and replica cases.
- \`tests/test_raven_fork_evidence.py\`: two-branch verification and tampering cases.

The GitHub Actions workflow invokes all RAVEN-002–004 tests on research branch
pushes. **Do not claim these newly added tests passed without a completed run.**

## Next research gate

Introduce independently verifiable, append-only consistency proofs and
client/witness exchange of checkpoint receipts in a bounded state-space
simulator. Add Byzantine equivocation, offline clients, asymmetric network
partitions, signing-key rotation, and server crashes. Measure detection
probability/latency, bandwidth, state growth, denial-of-service cost and
availability impact. Keep this isolated from production CryptoWall.
