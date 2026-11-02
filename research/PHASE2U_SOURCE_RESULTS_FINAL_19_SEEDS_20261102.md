# Phase 2U — Complete 19-seed prospective source registry (2026-11-02)

**This report is exclusively about classical candidate generation.**
The 19 original source jobs complete a contiguous, predeclared seed prefix.
The twelfth accepted candidate was found on **seed 41143**, so generation
**must stop there**. Do not run or select any later registered source seeds.

| Seed | Original source result | Exact-metric hits | Random-swap fallback proposals | Artifact ID |
|---:|---|---:|---:|---:|
| 41003 | accepted | 65 | 0 | 13113599556 |
| 41011 | ineligible | 0 | 0 | 13136426780 |
| 41017 | accepted | 85 | 0 | 13134649849 |
| 41027 | ineligible | 0 | 0 | 13136142649 |
| 41039 | accepted | 114 | 0 | 13136730329 |
| 41047 | ineligible | 0 | 0 | 13135489405 |
| 41051 | accepted | 137 | 0 | 13137865391 |
| 41057 | ineligible | 0 | 0 | 13137606727 |
| 41063 | accepted | 93 | 0 | 13137216809 |
| 41071 | ineligible | 0 | 0 | 13140663528 |
| 41077 | accepted | 106 | 0 | 13140843593 |
| 41081 | accepted | 36 | 0 | 13140713382 |
| 41089 | accepted | 6 | 3 | 13140388590 |
| 41101 | ineligible | 0 | 0 | 13142727617 |
| 41113 | accepted | 96 | 0 | 13141899471 |
| 41117 | ineligible | 0 | **7** | 13142147789 |
| 41131 | accepted | 123 | 0 | 13141968078 |
| 41141 | accepted | 91 | 0 | 13147734812 |
| 41143 | accepted | 61 | 0 | 13149120287 |

## Independent verification, completed

An independent standard-library Python audit of all nineteen
original ZIP archives, using no repository classical evaluator, found:

- **19 valid source receipt SHA256 seals**, unique source seeds in the
  exact frozen order, and exactly **340 classical evaluations per seed**.
- **12 accepted selected 8-bit permutations** and **7 valid ineligible
  source outcomes**. Exactly one candidate per successful seed counts.
- For all accepted S-Boxes, independently recomputed **NL=100,
  differential uniformity=8, max |LAT|=56, algebraic degree=7**, and
  the claimed SAC values match the original 256-byte permutations.
- **12 distinct SHA3-256 candidate fingerprints; no pair of retained
  candidates is equivalent via S(x XOR a) XOR b**.
- Exactly **10 bounded random-swap proposals** over all nineteen seed
  runs: 3 on accepted 41089 and 7 on ineligible 41117. No generator
  crashes or incomplete classical budgets in the new version.
- **6,460 classical evaluations** and **zero neural trainings**.

Seed 41141 candidate SHA3-256:
`021b4db023aecb049c10b3bb8ecba645b135097e1bc61ca799801a1aec37bdec`
with SAC 0.499267578125.
Seed 41143 candidate SHA3-256:
`00c50e20ea55e3b344eff3a12cda24db9c30400e511d920e12dd106d83721966`
with SAC 0.501220703125.

**Source audits do not establish cryptographic resistance** or
mathematically rule out broader affine-equivalent families, common
ancestral correlations, or adversarial keys.

## Final panel admission and provenance reproduction — distinct gates

**Gate A (independent classically valid selected candidates): PASS** for
the twelve in the original ZIPs, with the limitations above.

**Gate B (repository exact-source admission): pending.**
The dedicated [final source admission workflow](https://github.com/Chatnoir01/ml/actions/runs/41460802079)
must rehydrate the *original source artifacts* from six GitHub Actions
runs and feed **exactly the first nineteen receipt JSONs** into the
repository's `phase2u_panel.aggregate()`. It must reject historical
and Phase 2T-v1 exact and XOR-related copies, validate strict
classical-metric replay and refuse extra/missing seeds. It emits a
source-panel receipt, not neural predictions.

**Gate C (independent full source search replay): pending.**
The separate [41003 source replay](https://github.com/Chatnoir01/ml/actions/runs/41460158043)
must independently regenerate all 340 classical evaluations from its
registered seed on another GitHub runner and match the original source
SHA256, starting population digest and proposal transcript digest.
One seed replay strengthens reproducibility evidence for that seed,
but is NOT proof that all nineteen trajectories were independently
replayed.

**Gate D (classical prediction precommit): NOT yet performed.**
Only after Gate B passes may a separate research action compute and
freeze the classical one-bit ranking, publish its SHA-256 receipt in
an independently reviewable commit, and verify no Phase 2U neural
labels have been generated. Do **not** train any neural model yet.

No claims about a novel primitive, AES, cipher security, post-quantum
resistance or confirmed neural generalization are established.
