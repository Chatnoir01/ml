# TPM held-out 64-seed confirmation — GitHub source-run result

**Completed 2026-10-23.** Research-only finite TPM simulation.
This document is an **outcome appendix added after the frozen protocol**;
it does not modify the original preregistration
[`TPM_HELDOUT_64_PROTOCOL.md`](TPM_HELDOUT_64_PROTOCOL.md).

## Verified provenance

- Draft PR: [#147](https://github.com/Chatnoir01/ml/pull/147).
- Exact tested head: `b3285a59f19bed17a9aedbe8831441da746e4c40`.
- GitHub Actions run: [39932754689](https://github.com/Chatnoir01/ml/actions/runs/39932754689), **completed SUCCESS**.
- Specialized 64-trial job ID: `120344790698`, **completed SUCCESS**.
- Artifact ID `12493176136`, name `tpm-heldout-64-python311`, retained by GitHub through 2026-12-22, SHA-256 of artifact archive `4084743ba82cd52106d03f2a6d04f1c34fc16bafd4b15a1b4c1375b44669cab7`.
- CI verified fixed 64 trial indices, complete per-trial field schema, preregistered plan SHA-256 `0872aa224297a9a9630cd7f58448b5254ff12064f651fcfd787424be5bb2ba06` and TPM protocol SHA-256 `dfb640df5159f38db9cc05706e0d2583273ffdb49d608f324c05d233891e9452`.
- Dedicated TPM smoke CI run [39932754551](https://github.com/Chatnoir01/ml/actions/runs/39932754551): **SUCCESS**. Earlier Phase 0 CI run [39932690841](https://github.com/Chatnoir01/ml/actions/runs/39932690841): **SUCCESS**. The separate exact-head Phase 0 run [39932754524](https://github.com/Chatnoir01/ml/actions/runs/39932754524) was still **in progress** when this appendix was initially authored; do not infer its outcome.

## Predeclared outcomes from CI logs

Alice/Bob synchronized in **64/64** trials, with **zero censored trials**.
Attack success means that **at least one** candidate's entire private
weight state matched Alice's state **at the first legitimate
synchronization**. The private equality oracle is available to the
simulator, **not to communicating parties or attackers**.

| Method | Exact matches | Rate | Descriptive Wilson 95% interval |
| --- | ---: | ---: | ---: |
| Cooperative majority heuristic, 9 candidates | 30 / 64 | 46.88% | 35.18–58.93% |
| Independent geometric attackers, 9 candidates | **53 / 64** | **82.81%** | 71.79–90.12% |
| Genetic-style branching heuristic, 16 candidates | 2 / 64 | 3.12% | 0.86–10.70% |
| Independent geometric attackers, 16 candidates | **58 / 64** | **90.62%** | 81.02–95.63% |

### Exactly two prespecified paired contrasts

**C1: 9 cooperative majority vs 9 independent geometric candidates**

- Both attackers succeeded on **29** trials.
- Cooperative-only success on **1** trial.
- Geometric-only success on **24** trials.
- Neither succeeded on **10** trials.
- Paired difference (cooperative minus geometric): **-23/64 = -35.9375 percentage points**.
- Two-sided exact McNemar `p = 0.0000015497207641601562`.
- Holm-adjusted across C1 and C2: `p = 0.0000015497207641601562`.

**C2: 16 genetic-style branching vs 16 independent geometric candidates**

- Both succeeded on **2** trials.
- Genetic-only success on **0** trials.
- Geometric-only success on **56** trials.
- Neither succeeded on **6** trials.
- Paired difference (genetic-style minus geometric): **-56/64 = -87.5 percentage points**.
- Two-sided exact McNemar `p = 2.7755575615628914e-17`.
- Holm-adjusted across C1 and C2: `p = 5.551115123125783e-17`.

These are results of the **specific frozen code and toy TPM** under an
exact-weight-at-first-sync criterion. Candidate **counts** were matched,
but CPU, total optimizer/update operations, memory, attack sophistication,
and access to real authenticated communication were **not** matched.
The low success of the genetic-style *local-field heuristic* does
**not** disprove published genetic cryptanalysis.

## Scientific interpretation

- The preregistered paired comparisons both favor independent
  geometric replication on this fixed finite-size toy TPM.
- Simply increasing candidate count from 9 to 16 also raises independent
  geometric exact-match success here, but this is **not a randomized,
  equal-budget superiority test** and should not be marketed as a new law.
- The practical research direction is to strengthen evaluation with
  **equalized operation counts, multiple TPM dimensions, independent
  cryptanalytic implementations and adversarial public-input/channels**.
- There is **no evidence of a usable secure neural key exchange**.
  Python `random.Random`, unvalidated information leakage, unprotected
  public parity transcript, privileged simulation detection, absence of
  key confirmation, and small model entropy make live deployment unjustified.
- Do not turn these findings into security guarantees for CryptoWall or
  replace vetted HPKE/AEAD constructions.

The original raw trial-level JSON is stored in the GitHub Actions
artifact for reproducibility, not inferred from this summary.
