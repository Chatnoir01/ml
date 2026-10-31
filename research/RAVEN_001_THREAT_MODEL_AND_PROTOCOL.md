# RAVEN-001 — Threat model and falsifiable research protocol

Status: **research proposal only**. Not a cryptographic product, protocol specification, security proof, or production recommendation. No user data, credentials, or real-world keys.

## 1. Research question

Can a recursive compartment-and-epoch architecture combine (a) cross-compartment compromise containment, (b) authenticated cryptographic policy transitions, and (c) rollback detection, while retaining competitive cost and security compared with established independent-key and ratcheting baselines?

**Novelty is unproven.** Hierarchical KDFs, domain separation, key ratchets, key transparency, authenticated state machines, monotonic counters, and group protocols already exist. A successful demonstration must isolate a new property, composition theorem, or meaningful engineering advantage over strong baselines.

## 2. Definitions

Compartment i at epoch e is modeled by:
C[i,e] = (id_i, e, policy_digest, local_secret, session_state, authorization_state).

- Root authority authenticates policy and identities; it is **not** a universal decryption root.
- Isolation experiment uses independently generated compartment secrets. Deriving all compartments from one compromised master does not establish isolation.
- Per-use keys may be derived using HKDF with unambiguous domain separation:
  K[i,e,u] = HKDF(local_secret[i,e], info = encode("RAVEN-001", id_i, e, u, suite_id)).
  This alone does NOT deliver post-compromise recovery.
- Epoch updates requiring recovery incorporate fresh, independently sourced secret material through a reviewed key-agreement/ratchet mechanism. Erasure assumptions must be explicit.
- A transition record binds old/new epoch, old/new policy digests, suite identifiers, compartment ID, transcript hash, and authenticated authorization.
- Rollback resistance requires an external trusted monotonic anchor or consistency service under a stated threat model. A local counter or hash chain stored beside compromised state is insufficient.
- Cross-device consistency and split-view resistance are **out of scope** until a concrete consistency protocol is specified.

## 3. Adversary and security boundaries

Attacker may:
1. Record, delay, reorder, replay, mutate, and inject ciphertexts.
2. Obtain a complete snapshot of compartment B's local secrets and session state at epoch 4.
3. Restore earlier disk snapshots and manipulate untrusted application storage.
4. Substitute unverified public keys and propose weaker suites.
5. Observe public metadata and message lengths.

Attacker may NOT, for the initial narrow experiment:
- Break assumed secure primitives (AEAD, HKDF, approved KEM).
- Compromise an independent trusted monotonic anchor or signing authority.
- Compromise other compartment secrets unless a test explicitly expands the compromise set.
- Access fresh entropy introduced after compromise and not exposed to the attacker.

These exclusions are **assumptions**, not security achievements. Later experiments must relax them.

## 4. Claims to test (not yet proven)

I1 — Isolation: Given full state of B at epoch 4, attacker cannot derive A/C encryption keys solely from B's state, assuming independent secrets and secure KDF.

I2 — Authenticated transitions: Unauthorized changes to policy, suite, compartment ID, epoch, or transcript must be rejected.

I3 — Replay: Repeated accepted messages must not cause duplicate application actions; requires durable application/session anti-replay state. Stateless envelope decryption may still succeed twice.

I4 — Rollback: Restoring a stale local snapshot must be detected **only when** the trusted monotonic anchor retains a newer epoch. Without this anchor, no rollback guarantee is claimed.

I5 — Post-compromise recovery: After B compromise, secrecy of subsequent messages is regained only following a fresh authenticated secret contribution that attacker cannot obtain, with explicit state erasure and authentication assumptions.

I6 — Algorithm agility: A migration to a stronger suite must not be silently downgraded by attacker-controlled negotiation; authenticated policy binds permitted suites and migration state.

## 5. Baselines and controls

A: Naive hierarchy with a single master secret; compromise master and observe scope of exposure. This is a negative control, not a competitive reference.

B: Independently generated compartment keys plus domain-separated per-use derivation and standard AEAD.

C: Established authenticated ratchet/reference protocol, with independently reviewed implementation and documented assumptions. Do not claim equivalence to Signal/MLS without implementing the actual protocol.

D: Experimental RAVEN composition (not yet implemented).

Compare B/C/D on identical threat scenarios. RAVEN must beat B/C on a specified metric/property to support a novelty claim.

## 6. Experiments

E01 Cross-compartment compromise: create A/B/C; expose B epoch-4 state; attempt to derive A/C keys and decrypt A/C test ciphertexts. Record exact secret access and attacker capabilities.

E02 Epoch compromise: record B epochs 1–8; expose epoch-4 state; test decryptability before/after epoch 4. Distinguish backward secrecy from post-compromise recovery.

E03 Transition forgery: mutate each authenticated field, swap policy digests, replay old authorization, and inject unauthorized suite downgrade. Expected result: rejection before any application action.

E04 Rollback: restore epoch-2 local state after trusted anchor reaches epoch 5. Repeat without anchor as negative control. Do not assert rollback resistance without an independent anchor.

E05 Anti-replay: submit same authenticated message twice, restart application, resubmit; check persistent replay database and atomic commit of action+replay marker. Distinguish decryption from business-action acceptance.

E06 Cost: report ciphertext overhead, key/state size, latency p50/p95/p99, CPU and memory across payload sizes (0, 1KiB, 1MiB), compartment counts (1, 10, 1000), and epoch transitions. Record hardware, library versions, sample counts, confidence intervals.

E07 Hybrid negotiation: verify strict classical/hybrid version separation, backend failure closed, authenticated policy selection, and key-substitution rejection at the trust layer.

## 7. Pass/fail gates

- Each claimed invariant has at least one adversarial negative test and a corresponding positive control.
- Every accepted transition has a validated authorization and monotonic state commitment under the chosen trust model.
- No use of neural or evolutionary primitives for production encryption.
- No global success score based solely on round-trip tests or unsuccessful learned attackers.
- Document any assumption that would invalidate a result if relaxed.
- Independently review the reference protocol, security game definitions, and implementation before security claims.
- Fuzz malformed envelopes and transition records; use independent interoperability vectors and reproducible locked dependencies.
- **Any failure of an invariant blocks advancement of the experimental construction; it does not imply an exploitable vulnerability in the separate CryptoWall v1 branch.**

## 8. Immediate engineering sequence

1. Build a pure state-machine model with no real encryption and executable invariant tests.
2. Add property-based state-machine tests for transition authorization, stale state, and compromise scope.
3. Add a reference implementation using vetted primitives, isolated from `src/cryptowall/`.
4. Compare against independently generated keys and a vetted ratchet baseline.
5. Conduct an external cryptographic review before any integration or deployment.

## 9. Explicit non-claims

No novel primitive, no provable security, no quantum safety for the complete protocol, no guaranteed post-compromise security, no production deployment approval, no independent audit, and no evidence of superiority over established protocols at this stage.
