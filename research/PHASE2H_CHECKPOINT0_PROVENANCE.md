# Phase 2H — Checkpoint-0 comparability and reproducibility gate

Status: **diagnostic provenance check, not a cryptographic improvement claim**.

## Frozen scientific context

The official Phase-2G adaptive experiment is locked, including its negative
verdict `phase2g_adaptive_coevolution_not_supported`, original seeds, settings
and held-out H. Phase 2H must not retroactively tune, regenerate or silently
replace the source data.

Phase-2H PR #127 identified a serious pre-adaptation A/F state-hash discrepancy:
five evolution seeds' checkpoint-0 model state hashes matched; for four seeds
the initial 16-model hashes did not match. This finding must be distinguished
from training-receipt hashes, which embed the A/F **arm label** and can disagree
even when model states are byte-identical.

## Why this matters

At generation zero the A and F curricula are intended to be identical, and
the frozen T/M training seed grids are shared. The deterministic trainer's
`train_shared_checkpoint_model` function passes a canonical curriculum,
difference and dataset/model seed to the data generation/optimizer; the arm
identity is metadata, not an intended numerical training input.

**Equal declared inputs are not proof of identical actual data, model weights,
runtime libraries, BLAS execution or processor state.** Conversely, different
SHA-256 hashes prove that the serialized model states recorded differ, not
which implementation or environment caused them to differ.

## New receipt-only test

`phase2h_baseline.audit_checkpoint0_baseline` validates:

1. One checkpoint-zero receipt per arm, with the same canonical 20-candidate
   curriculum, verified against its own SHA-256 digest.
2. Complete, unique 2-difference × 8-replicate state-hash grids.
3. Per-model T/M seeds matching one another *and* the preregistered seed blocks.
4. The checkpoint-level declared T/M arrays matching the same frozen blocks.
5. Mismatch counts for each difference and replicate. The computation
   excludes arm-tagged training-receipt hashes.
6. Distinct statuses: input mismatch, insufficient proof, matching inputs /
   matching model hashes, or matching inputs / different model hashes.

The diagnostic is applied to **all nine paired seeds**, includes no held-out
data, and is re-executed in reverse input order in GitHub Actions. Its JSON
record and aggregate counts appear in the generated Phase-2H result. A
dedicated CI step logs only nonsensitive aggregate counts.

## Interpretation firewall

If the frozen receipt data prove matching declared inputs but show different
model-state hashes, this remains a **reproducibility/comparability anomaly**.
It is NOT evidence that adaptive learning caused the mismatch, nor proof of a
particular numerical or data-generation defect.

To investigate separately, first preregister a minimal deterministic
reproduction with fixed data hashes and dependency versions, identical runtime
and controlled BLAS threading; then compare dataset hashes and serialized model
state hashes across reruns and environments. That experiment is **not** executed
or authorized by this PR.

No post-hoc change to Phase 2G conclusions is permitted. Do not promote a
causal H1/H2/H3/H4 claim or authorize Phase 2I from this audit alone.
