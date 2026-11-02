# Phase 2T — Source-generation execution ledger (observations only)

**Research provenance note. Do NOT edit the original preregistration thresholds.**

The predefined program targets exactly 12 candidates satisfying
NL=100, DU=8, max |LAT|=56, degree=7, SAC within 0.05 of 0.5. Each
registered new seed is allowed exactly 340 classical evaluations.
Candidates are selected using classical metrics only, before any neural
training or measurement. Source seed failures are retained.

## Confirmed pilot result

| Field | Verified outcome |
|---|---|
| Date | 2026-11-02 |
| Source seed | 31001, first in frozen 24-seed order |
| Classical evaluations | 340 (GitHub job assertions passed) |
| Neural trainings | 0 |
| Source status | `ineligible` (no exact-metric candidate in evaluated ledger) |
| Generator scientific SHA-256 | `5b5d4a1dd650bb8aa606a2ca610db6b5417278374444cd156a67be93966cf376` |
| GitHub Actions | `41371224069` |
| Artifact ID | `13109089315` |
| Artifact name | `phase2t-classical-seed-31001` |
| Job | completed successfully; result itself is a valid negative source outcome |

Run: https://github.com/Chatnoir01/ml/actions/runs/41371224069

**This is a source-generation outcome, NOT a neural prediction evaluation.**
The artifact source should be downloaded and compared with a deterministic
independent rerun to upgrade its provenance from merely workflow-generated
to independently reproduced. An SHA-256 alone does not prove authenticity.

## Next four seeds initiated but NOT yet interpreted

Registered source seeds `31013`, `31019`, `31033`, `31039`
were dispatched in the fixed batch-B research workflow.
At the time of this record, their output classifications had NOT been
verified, therefore do not count them as accepted or rejected.

## Budget and interpretation

- The entire frozen registry contains 24 seeds: at most **8,160**
  classical evaluations at 340 per seed, and **96** separately gated
  neural trainings **only after** a complete 12-S-Box panel and a publicly
  frozen prediction receipt.
- The one-seed ineligible result is not evidence that the entire
  24-seed protocol is infeasible. Conversely, the historical Phase 1O
  JOINT-target success rate does NOT imply that 12 exact
  (NL, DU, LAT, degree) matches are guaranteed within this new registry.
- After the first twelve exact-metric successful seeds, stop; no
  artificial additional selection or neural score-based curation.
- If 24 seeds are exhausted without 12 accepted candidates, declare
  `PANEL_INCOMPLETE_DO_NOT_RUN_NEURAL` and record the failed sampling
  design. Do not relabel modified rules as a confirmation of Phase 2T.
- Expensive candidate-generation workflows were changed from automatic
  PR-triggered execution to explicit manual `workflow_dispatch` after
  the initial pilot and batch were initiated. This avoids rerunning the
  same classical search on unrelated commits.
- `phase2t_provenance.py` now provides pre-training plaintext-source
  and model-initialization fingerprints; its tests are software checks,
  not completed neural training.

## Retrospective artifact audit and seed-31013 incident (2026-11-02)

The four original GitHub Actions ZIP artifacts were downloaded from their
provider records and independently recomputed, *without importing the project
classical evaluator*, using `scripts/phase2t_audit_artifacts.py`.

| Seed | Executed outcome | Receipt SHA256 checked | Independently recomputed classical properties |
|---:|---|---|---|
| 31001 | ineligible, 0 exact hits | PASS | No candidate to evaluate |
| 31013 | **unhandled generation failure** | **NO RECEIPT** | Generator exhausted unique proposal attempts |
| 31019 | accepted, 38 evaluated exact-metric hits | PASS | NL=100; DU=8; maxLAT=56; degree=7; SAC=0.503173828125 |
| 31033 | ineligible, 0 exact hits | PASS | No candidate to evaluate |
| 31039 | accepted, 111 evaluated exact-metric hits | PASS | NL=100; DU=8; maxLAT=56; degree=7; SAC=0.500244140625 |

- Batch-B run: https://github.com/Chatnoir01/ml/actions/runs/41371608468
- Accepted seed 31019: archive ID `13110002017`, fingerprint `00b8f73392137f3787850405fbfa831b5bac659d61026dc95c403b1230ed6147`, receipt `ae948c7a341b749246b669aa957e0c1367ba83b6a41891360b8a82ced91b2f1b`.
- Accepted seed 31039: archive ID `13109542695`, fingerprint `0373455d13417e7e1efb5feb953961dc9dbc58eac3b62730f7ea0556567020e2`, receipt `de25886d04aa61c06d2d87df3caf53f36c5cd587569beb1b4ca95e3cec98f840`.
- Ineligible seed 31033: archive ID `13109483030`, receipt `1bc02bbb47e6e0eea5d2a4adab7873ba3731a311636c8e452bc19ed51c1e5880`.
- Ineligible seed 31001: archive ID `13109089315`, receipt `5b5d4a1dd650bb8aa606a2ca610db6b5417278374444cd156a67be93966cf376`.

**Critical scientific blocker:** seed 31013 failed after the Phase-1O
`_collect_unique_batch` generated no globally unique proposals across more
than 512 consecutive parent attempts. The source job ended with
`RuntimeError("unable to generate globally unique Phase 1O proposals")`,
rather than completing 340 unique evaluations or recording a conforming
ineligible outcome.

It is **invalid** to skip this missing ordered seed, call it a completed
340-evaluation failure, or reuse two later accepted candidates as if an exact,
contiguous v1 source ledger existed. As written, **the original v1 prospective
panel is BLOCKED**. Keep its records and do not unblind or perform neural
training under this version. A deterministic algorithmic rescue or new source
registry must be a new, explicitly versioned prospective protocol, with all
previous observations disclosed as development information. The v1 negative
and positive outcomes must not be retrospectively blended with new-version
results.

This independent audit checks returned output permutations and mathematical
metrics, not the origin of the initial population or fidelity of the full
optimization path. A full fixed-seed source replay remains a distinct gate.

No new neural result, no scientific confirmation and no real-world
cryptographic security result are established here.
