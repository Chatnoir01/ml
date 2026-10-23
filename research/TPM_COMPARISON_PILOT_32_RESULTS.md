# TPM five-arm paired pilot — local reproduction (2026-10-23)

**Status: preliminary local reproduction, not yet independently validated by
the exact-head GitHub Actions full-pilot job. Do not present as a
cryptographic security claim or a certified genetic attack.**

The local reproduction reconstructed the Python algorithm and frozen
parameters from PR #146, rather than running a direct GitHub checkout.
It matched the earlier 8-trial TPM reference exactly:
- First eight Alice/Bob synchronization times:
  `[91, 118, 55, 81, 86, 48, 36, 89]`; median **83.5**.
- First eight geometric attacker matches **4/8**, random-flip **1/8**,
  naive **0/8**.
- The source-of-truth confirmation is the new `paired-full-pilot`
  GitHub job on PR #146. It runs the repository code and saves its own
  unedited machine-readable report artifact.

## Frozen 32-trial local observations

Plan SHA-256:
`f008b0327a1ef0b97c8b1c56815aa004e706bdb4af5553a33de3eadeda345280`

TPM protocol SHA-256:
`862bb61917b8848f60f3ff21f688c44980d0afdb838d497f33be55412f1b77b0`

Legitimate Alice and Bob synchronized in **32/32** trials, with
**zero censored** trials and **94** median synchronization rounds.
Each arm uses the same legitimate initializations and public stimuli.

| Attack | Exact state matches / 32 | Proportion | 95% descriptive Wilson interval |
| --- | ---: | ---: | ---: |
| Naive single Eve | 2/32 | 6.25% | 1.73–20.15% |
| Geometric single Eve | 15/32 | 46.88% | 30.87–63.55% |
| Random flipping single Eve | 7/32 | 21.88% | 11.02–38.76% |
| Cooperative majority heuristic (9 Eves) | 18/32 | 56.25% | 39.33–71.83% |
| Bounded genetic-style branching (16 candidates) | 2/32 | 6.25% | 1.73–20.15% |

### Interpretation safeguards

1. **This finite-size TPM has demonstrated attack success**. We cannot
   infer that synchronized TPM weights constitute a secure shared secret.
2. A majority ensemble uses **9 Eves**, genetic-style branch uses **16
   candidates**, whereas geometric/naive/random flipping use one. This
   is **not an equal-resource or equivalent-attacker comparison**.
3. The genetic-style implementation uses a simplistic local-field selection
   heuristic; its low success does **not** establish that published
   genetic attacks are weak.
4. Even with 32 paired trials, success-rate uncertainty is substantial.
   Wilson intervals do not cover selection bias, active attacks,
   different TPM dimensions, RNG issues or protocol compromise.
5. Results describe exact private-weight equality **as measured by a
   privileged simulation oracle**. Public participants cannot use that
   oracle to verify real synchronization.
6. No production key derivation, authenticated key agreement, crypto
   assurance, or integration with CryptoWall was performed.

**Reproduction:** the new PR workflow executes
`python scripts/run_tpm_comparison.py --trials 32`
from the exact repository checkout and uploads
`tpm_32_trial_report.json` as a GitHub Actions artifact; the local
JSON reproduction is available separately in the conversation.
Await the exact-head workflow outcome before replacing this
preliminary report with a verified source-run receipt.
