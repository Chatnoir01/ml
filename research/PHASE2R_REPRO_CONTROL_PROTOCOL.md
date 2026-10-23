# Phase 2R — Prospective checkpoint-0 reproducibility control

**Status: preregistration and receipt verifier ONLY — SCIENTIFIC EXECUTION LOCKED.**

Owner issue: #130. Antecedents: Phase-2H #121 and stacked diagnostics PRs #123–#129.

## Motivation and prior observation

The original Phase-2G A/F artifacts are frozen. Analysis of model-state SHA-256
hashes shows *5 of 9* paired evolution seeds matched at checkpoint 0; *4 of 9*
did not, despite matching declared curriculum fingerprints and T/M training
seed registries. This is a **baseline reproducibility/comparability anomaly**,
not a demonstrated explanation for Phase-2G's negative adaptive-coevolution
verdict. Neither Phase 2R nor this implementation changes the old experiment.

## Scientific question and frozen hypotheses

Can a fixed checkpoint-0 model-training input produce byte-identical datasets,
model initializations, and final serialized model weights across:

- two separate A-labelled runs (A1, A2) in the same controlled environment;
- two separate F-labelled runs (F1, F2) in the same environment;
- cross-arm matched repeated runs (A1/F1, A2/F2) with otherwise identical
  curriculum, data generation and initialisation seeds?

**Primary endpoint**: *all* 16 model cells (difference 1 or 256 × replicates
0–7) must show byte-identical train/validation/test payloads, initialization
bytes, and serialized model bytes across all four preregistered comparisons.
No average-case, majority or post-hoc tolerance can promote a failed cell
to a pass. Only checkpoint 0; no GA evolution or held-out evaluation.

This is an exact-byte reproducibility test, not a cryptographic security test.

## Pinned synthetic curriculum delivered

The diagnostic-only file `research/fixtures/phase2r-synthetic-curriculum-v1.json`
now provides the **actual 20 × 256 candidate bytes**, not only an RNG seed.
The recorded fixture is independent of historic 2G populations and does
**not** support retrospective regeneration of original model states.

- Fixture identity: `phase2r-synthetic-v1`.
- Generator disclosure: xorshift32/Fisher–Yates seeded by `0x26102023`,
  with the generated candidate **bytes themselves committed**.
- Canonical content SHA-256:
  `ca6eea1f554b1004ad69d0da828ae2fac5cdb5a4d1f5f6ab80e5787ce5c9a106`.
- Canonical Phase-2G-compatible curriculum SHA-256 (sorted SHA3-256
  fingerprints joined by LF):
  `09e94da031992240d857a139768445c042cb712abf866f15084300a4a267e8a2`.

The non-executing fixture reader validates both digests, exactly 20
distinct bijective S-Boxes and exact byte arrays. Phase-2R receipt validator
binds this curriculum digest and fixture ID into its protocol SHA;
alternative curricula cannot silently pass the same control.

This input fixture is **not a demonstration of cryptographic strength**.
Its sole role is to provide fixed, comparable bytes for future
reproducibility measurements. Real experiment authorisation, pinned
model-initialisation bytes/serializer, runtime provenance and dependency
locking remain outstanding.

## What must be frozen *before* any real training

1. An **independent 20-S-Box synthetic input fixture**: actual canonical candidate
   bytes, fingerprints and SHA-256, recorded in a separately committed/pinned
   fixture. A SHA-256 digest alone is insufficient to reconstruct the inputs.
   If reproducing a *historical* frozen checkpoint-0 pool, prove the original
   candidate bytes and provenance; do not generate or infer them from hashes.
2. Exact experiment implementation commit, dependency lock digest, Python,
   NumPy, OS/architecture, CPU/BLAS provider/version and thread limits.
3. Frozen checkpoint-0 dataset/model seeds from the Phase-2G seed registry,
   two input differences (1, 256), eight replicates, the model architecture,
   training/validation/test splitting, order and precise serialisation schema.
4. Two **independent** repeats per arm, same host/runtime for the first
   protocol run. New cross-host experiments require a **separately defined**
   execution protocol: differences in environment make byte comparison
   scientifically incomparable under the current contract.
5. A source-linked, append-only record of authorisation and execution start,
   acquired before generating any real results. **This PR is not approval.**

## Evidence contract

The pure Python validator in src/adversarial_sbox/phase2r_repro.py defines
PROTOCOL and its SHA-256, MODEL_GRID, RUN_GRID and PAIR_GRID. A **future**
externally generated receipt bundle contains the exact protocol_sha256 and
all four labelled runs. Each run must contain:

- canonical 20-candidate curriculum SHA-256;
- runtime metadata including source SHA-256, dependency lock SHA-256,
  Python/NumPy/platform, BLAS and five thread-limit variables;
- exactly 16 distinct (difference, replicate) model receipts;
- each model's declared frozen T/M seeds and curriculum digest;
- **byte hashes** of generated train/validation/test data; initialization
  bytes; final serialized state bytes.

The canonical ciphertext-pair serializer is implemented in
src/adversarial_sbox/phase2r_serialization.py. It domain-separates each
train/validation/test split, preserves row order and packs the two ciphertext
blocks as uint32 little-endian and the binary label as uint8. It is covered by
synthetic endian/order/label/split regression tests and does not generate data.
The future model-initialization and final-state serializers, exact candidate
fixture bytes and environment lock still require a separate preregistration
gate. The verifier cannot attest supplied byte hashes were produced honestly.

The serializer that will generate those hashes must itself be frozen and
versioned *before* execution. Do **not** hash a Python repr or platform-
dependent array representation and call that comparable across environments.
Pin sample order, dtype, shape, endian representation, labels, data structure
and serialization bytes. Capture actual initialization **before first optimizer
step** and final serialized weights after the final step.

Only **non-sensitive metadata and digests** belong in the public result; never
capture environment secrets, API credentials, raw citizen messages or
unconsented files. This research control needs no credentials.

### Predeclared comparison priority

For each pair, if runtime and curriculum do not match, status is
INCOMPARABLE_DIFFERENT_RUNTIME_OR_CURRICULUM. Otherwise:

1. Unequal dataset bytes -> FAIL_DATA_BYTES_DIFFER.
2. Equal datasets, unequal initialization bytes ->
   FAIL_INITIALIZATION_BYTES_DIFFER.
3. Equal datasets/initializations, unequal model bytes ->
   FAIL_SERIALIZED_MODEL_BYTES_DIFFER.
4. All byte hashes match -> PASS_REPRODUCIBLE_BYTES_IN_CONTROL.

Missing, duplicate, malformed or unhashed evidence raises ValueError, not
PASS. Every pair and all 16 cells are reported; no cherry-picking. The overall
PASS requires all four pairs to pass, but **even PASS cannot explain the
historical 4/9 anomaly or prove broader determinism**.

A contradictory state hash without identified data/initialisation mismatch
points to a *potential numerical/runtime or hidden-state issue*, not to a
proven cause. Thread constraints in receipts must be checked against actual
runner state at collection time; the validator cannot independently attest
the truthfulness of supplied metadata.

## Verification before executing any scientific run

Run only tests of the **verifier** with artificial SHA fixtures:

    python -m pytest tests/test_phase2r_repro.py

The workflow phase2r-repro-contract.yml performs these tests. It executes no
training and consumes no old or new experimental held-out data. Its green status
means the receipt checker operates on synthetically constructed cases,
**not** that the Phase-2R scientific experiment succeeded.

## Hard firewall and release gate

- Never launch Phase 2R training merely by opening/merging this PR.
- Do not alter old Phase-2G cells, model states, experimental thresholds,
  original verdicts, held-out data or SHA-256 records.
- Do not infer a causal H1/H2/H3/H4 explanation from a hash comparison.
- Do not authorize Phase 2I, a new cipher claim or a production deployment.
- Before a future controlled run, obtain owner/scientific authorization,
  a separately frozen fixture + serializer + lockfile + runtime manifest,
  then review leakage/feasibility and the total exact execution budget.

**Current milestone = verification instrumentation completed, not a new
experiment or new scientific discovery.**
