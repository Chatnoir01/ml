# RAVEN-007 — Crash-only durable vote intent before Ed25519 witness signature

**Research experiment, not a consensus or secure real-world witness service.** This is a separate version stacked on RAVEN-006, which correctly demonstrated that losing a single RAM vote after restart permits the same honest key to sign two conflicting child receipts.

## Falsifiable question and precise threat model

Can we prevent accidental double-signing **across process crashes** by using an exclusive local file vote intent, a completed `fsync()` on that file and on its parent directory **BEFORE** calling the Ed25519 signing primitive?

Assumptions: single trusted POSIX local filesystem and durable crash semantics, non-malicious kernel and storage controller, a trusted pre-created private directory, exclusive physical custody of each Ed25519 key, no malicious file replacement, no shared-key replica, no history rollback, fixed RAVEN-006 pinned genesis and one child epoch. This study does NOT prove rollback resistance, anti-Sybil governance, physical power-cut durability, distributed consensus or multi-epoch correctness.

No insecure file-permission fallback: reject group/world-writable directory, root symlinks, missing O_NOFOLLOW or O_DIRECTORY, nonregular/symlink vote records, unreadable/oversized/corrupt records and conflicting existing vote intents. Empty or partial files are **fail-closed, not automatically cleaned up**; that preserves safety but may sacrifice availability.

## Protocol under test

For a cryptographically verified issuer-signed, rooted RAVEN-006 child receipt:

1. Construct a domain-separated canonical identity containing roster witness ID/key, issuer, namespace, compartment, pinned genesis and parent epoch/commitment.
2. Hash that PARENT identity to one deterministic journal filename; competing child proposals MUST contend for the same file.
3. Atomically establish exactly one intent using `O_CREAT | O_EXCL | O_NOFOLLOW`. Record its original signed-receipt identifier and a simple, **non-authenticating** SHA-256 of the record.
4. Flush all bytes and `fsync` the file inode, then `fsync` the containing directory. An existing accepted record must also be independently fsynced before signature, to avoid a race with an unfinished writer.
5. Verify any preexisting journal belongs to exactly the same parent and exactly the same receipt. Any other child, partial file or corrupted record is rejected.
6. ONLY AFTER the completed journal barrier, sign the identical receipt with Ed25519.
7. On restart and delivery loss, the same key may re-sign the same exact receipt idempotently; a different signed child for the same parent remains forbidden.

**Security boundary of the model:** the disk history is trusted and must not be deleted or restored from an older snapshot. Without an external monotonic anchor, an attacker controlling file backups can erase this recorded intent and force the same witness key to double-sign. The negative control in the tests intentionally exhibits that attack. A SHA-256 stored alongside an attacker-editable record provides NO anti-rollback security.

## Failure injection and expected outcomes

| Injected crash point | Disk state before signature | Expected restart behavior |
|---|---|---|
| Before exclusive create | No vote intent, no signature | Another child may be selected safely |
| After open, before write/fsync | Empty/partial intent; no signature | Any child rejected until trusted recovery |
| After file fsync, before directory fsync | Same intent bytes, no signature | Existing record is fully flushed again before re-sign |
| After directory fsync | Complete chosen-child intent, no signature yet | Same child may be signed, conflicting child refused |
| Before signature | Intent durable, no signature | Same child may be signed, conflicting child refused |
| After signature, before ACK | Intent durable; signature may be unacknowledged | Same receipt may be re-signed; conflicting child refused |

The suite also tests valid q=3/4 RAVEN-006 quorum certificates using the journal, corrupt records, forged issuer receipts, path symlinks, invalid permissions, and deliberate journal rollback.

## What remains open

- **Actual power-loss testing, filesystem-specific atomic/durability semantics and real parallel process fault injection.** Python exception injection alone is NOT a physical power-loss proof.
- Hardware- or independently anchored anti-rollback witness memory and a durable key-custody model.
- Signed member changes, roster rotations, higher epochs, network partitions and liveness.
- Cross-implementation wire formats; complete BFT consensus; independent security review.

## Original work remains immutable

This is in `research/raven_durable_witness_model.py` with separate tests `tests/test_raven_durable_witness_model.py`. The prior RAVEN-006 volatile witness, its negative rollback test and all previous research artifacts are retained. The new branch MUST NOT silently replace or hide the old failure.

**Scientific decision rule:** passing injected crash/restart tests demonstrates a narrow crash-only model improvement relative to volatile RAM; any conflicting signed receipt after a restart without malicious rollback falsifies the improvement. Even successful CI must not be interpreted as production security.
