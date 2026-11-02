# Phase 2U — Independent full classical-score replay (2 November 2026)

**Status:** 12/12 CLASSICAL SCORES AND BIT SELECTIONS REPRODUCED EXACTLY, and rank identical. **No new neural observations, no cipher security inference.**

## Evidence sources and distinction

An independent Python implementation (standard library ONLY, no import of the original ToySPN/SPN or original pair/bit-selector code) was run outside GitHub on 2026-11-02, using ONLY the original two JSON files extracted from GitHub Actions artifact **13185193738**. This independently implemented the exact public 32-bit four-round SPN with 11-bit rotations, five historical round keys, frozen `random.Random(seed XOR difference)` matched train/test 32-bit plaintext streams, train-only one-bit selection, signed independent heldout advantage, and arithmetic mean over input differences 1 and 256.

- Original GitHub freeze [run 41539098859](https://github.com/Chatnoir01/ml/actions/runs/41539098859), SUCCESS, produced frozen prediction **before any Phase 2U neural outcome**.
- Original artifact ZIP SHA-256: **`5084090f27fd225af5ae763055f022c4a83582a951fff1c73a4bb9d042551cd1`**.
- Original source panel SHA-256: **`512dd21d01617944047fd4e6f6ec2ae09daa68bc76d808837527a384148914ef`**.
- Original prediction receipt SHA-256: **`cd4bfbc9736ced13bdcf95c06f156d4244fbbdde65b05c51fb4e7958a21a30f4`**.
- Independently generated local audit JSON SHA-256: **`955cdfd1cd9b28209e48bff26b42002ff310303945a898daaa2f1792ee72ea61`**. Available in the conversation's accompanying downloadable artifact; not falsely claimed to be a cryptographically authenticated timestamp.
- An independently implemented reproducible auditor is now checked into `scripts/phase2u_independent_precommit_replay.py`; a separate source-receipt-bound CI run [41541767420](https://github.com/Chatnoir01/ml/actions/runs/41541767420) has been triggered. **Do not call that new exact-head CI green before its GitHub result completes.**

## Results from independently generated samples

| Predicted rank | Registered S-Box seed | Independently reproduced mean signed advantage |
|---:|---:|---:|
| 1 | 41089 | 0.204833984375 |
| 2 | 41039 | 0.199707031250 |
| 3 | 41141 | 0.196166992188 |
| 4 | 41003 | 0.178222656250 |
| 5 | 41063 | 0.173095703125 |
| 6 | 41081 | 0.170043945312 |
| 7 | 41017 | 0.167724609375 |
| 8 | 41077 | 0.163818359375 |
| 9 | 41143 | 0.160156250000 |
| 10 | 41051 | 0.157348632812 |
| 11 | 41131 | 0.150146484375 |
| 12 | 41113 | 0.133178710938 |

For all 12 selected S-Boxes, **both input differences, chosen output-bit indices, two signed heldout scores, final mean and ranking matched exactly**. Training and heldout plaintext blocks were disjoint for each difference, and no neural outcome labels were accessed. The classical ranking is not a neural performance measurement.

## Explicit scientific limits

- Does NOT demonstrate that neuronal distinguishability has the same ordering. Phase 2U prospective training remains 0.
- Does NOT fix the Phase 2R checkpoint-zero A/F model-state reproducibility problem or prove the original generation lineage for all 19 source seeds.
- Matching two implementations does not establish security of ToySPN, AES or any real cipher.
- New score computation must never be used to change the frozen ranking, feature selection, depth, key schedule, candidate ordering or statistical endpoints based on later neural results.
- The frozen study may be scientifically completed only after an **independently preregistered** neural experiment using new reserved seeds, signed run artifacts, model-init/data hashes and a predetermined statistical pass/fail rule. A negative generalization outcome is a valid result.

**No merge, no deployment, no neural unblinding performed.**
