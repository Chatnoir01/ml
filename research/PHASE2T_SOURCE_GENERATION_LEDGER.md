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

No new neural result, no scientific confirmation and no real-world
cryptographic security result are established here.
