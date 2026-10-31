# RAVEN-004 — Crash continuity, journal recovery, and fork experiments

**Research-only specification.** This is a RAM-based state-machine model and falsification harness, NOT a durable cryptographic service or a formal security proof. Do not place real secrets into it.

## Research question

Can a signed epoch/policy transition be recovered after interruptions without silently accepting rollback, when the device's local journal can diverge from a trusted, linearizable anchor?

**Important prior art:** IETF MLS RFC 9420 already defines authenticated epochs, transcript hashes, key schedules and competing Commit-message resolution (especially §14). A signed monotonic state machine alone is **not** a novel group messaging protocol. Reference: https://www.rfc-editor.org/rfc/rfc9420.html

## Model entities and explicit assumptions

- RAVEN-003 transition signed with Ed25519; its message binds namespace, compartment, current/next epochs, old and new policy digests, previous commitment, suite and event ID.
- Local state tuple: (namespace, compartment, epoch, policy, commitment).
- Local pending journal: (deepcopy(old state), signed transition).
- Shared trusted anchor: per-compartment tuple (epoch, commitment, policy_digest) with a **linearizable** check-and-advance operation.
- Recovery process can read both local state/journal and the anchor.
- The anchor is assumed trusted, survives crashes and cannot be rolled back. **The current implementation does NOT provide these properties.** It uses an in-memory object.
- The journal is likewise simulated in memory: it has no fsync, atomic rename, sector-write, storage-media, transaction, or power-failure semantics.
- Ed25519 authority key is assumed authenticated and uncompromised; identity and key rotation remain unsolved.

## Four transition stages and crash injection

1. **PREPARE:** verify transition against local state and anchor; save signed intent to journal.
2. **ANCHOR:** compare-and-set the trusted commitment to new epoch/policy hash.
3. **APPLY:** update local state to computed next state.
4. **CLEAR:** discard journal.

An injected exception may occur immediately following each stage. The same store and anchor objects are then supplied to a new machine instance, simulating restart.

### Recovery decision matrix

| Local state | Anchor state | Journal | Expected decision |
|---|---|---|---|
| Before | Before | Valid prepared intent | Abort uncommitted intent; retain before |
| Before | After | Valid signed intent consistent with After | Roll forward to After |
| After | After | Valid signed intent consistent with After | Clean journal |
| After | After | Empty journal | Ready |
| Before | After | Missing or invalid journal | **Reject** (cannot reconstruct safely) |
| Tampered | Any | Any | **Reject** |
| After | Before | Any | **Reject** |
| Before | Conflicting branch | Journal of another branch | **Reject** |
| Before | Before | Missing journal | Ready; no committed transition |
| After restored with anchor also rolled back | Also restored | Any | **NOT DETECTED** under this model |

These conditions are simulated algorithmic invariants, not proof of durable crash recovery on actual hardware.

## Adversarial experiments

- R04-E01: Inject crash at each of four stages, restart and classify recovery.
- R04-E02: Delete the signed journal after anchor advancement: reject, not silently reset.
- R04-E03: Tamper with signed journal, epoch or policy: reject.
- R04-E04: Restore stale local snapshot while anchor remains advanced: reject.
- R04-E05: Competing devices sharing one anchor: only one transition from an old epoch may commit; the other is rejected.
- R04-E06: Competing devices using **independent** anchors: both can accept different signed transitions at the same epoch. This is a **negative control demonstrating split-view vulnerability**.
- R04-E07: Simulate 10 sequential transitions with mixed crash points; verify anchor/local agreement after each recovery.

## What the model does *not* solve

1. **Crash durability and atomicity:** RAM-based objects are not a durable journal. In a production design, a storage-level threat model would specify fsync/rename barriers, anchor acknowledgment, and crash-atomic operations.
2. **Safety vs availability:** after an anchor commits but the signed journal disappears, fail-closed preserves the model's safety rule but may make the state unrecoverable without authenticated retrieval of historical intent.
3. **Distributed split view:** independent anchors cannot prove a shared canonical history. Gossip, witnesses, transparency/consistency proofs or consensus are outside RAVEN-004.
4. **Authorization availability:** compromised authority keys or compromised root of trust are out of scope.
5. **Cryptographic communication:** no AEAD, key exchange, key ratchet, erasure, forward secrecy, or post-compromise recovery implemented.
6. **Strong suite floor:** "legacy/classical/hybrid" tiers are test-policy labels, not a meaningful ordering of all cryptographic suites.
7. **Side effects:** no exactly-once durable application action transaction or anti-replay store.
8. **New scientific contribution:** not established; this is expected to overlap with event sourcing, WAL, append-only logs, key transparency, and trusted counters.

## Engineering targets for a future RAVEN-005

- A **durable** storage adapter with crash-injection using real files, fsync, and reproducible kill-point tests, with a clear trusted-anchor trust model.
- Authenticated checkpoint receipts and cryptographically verifiable fork *evidence* — without confusing signed proposals with finalized commits.
- Simulated Byzantine/split-view server plus gossip/witness consistency checks; quantify time-to-detection, witness availability, bandwidth and storage.
- Model checker/state-space exploration for concurrent transition/recovery schedules.
- Direct differential experiments against robust prior-art systems, especially MLS and key-transparency / append-only transparency constructions, to isolate an actual new guarantee or cost improvement.

## Testing

The source and adversarial suite are:
- \`research/raven_recovery_model.py\`
- \`tests/test_raven_recovery_model.py\`

Run: \`python -m pytest -q tests/test_raven_model.py tests/test_raven_signed_model.py tests/test_raven_recovery_model.py\`

Do **not** announce test pass counts until the corresponding runtime has actually returned a successful run.
