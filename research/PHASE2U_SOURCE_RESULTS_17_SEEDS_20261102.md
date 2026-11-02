# Phase 2U — Seventeen-source audited checkpoint (2026-11-02)

**Source-only experimental evidence; no neural training or predictive claim.**
Fixed source version: `phase2u_source_v1`. The first **17** source
seeds form a complete, ordered, non-skipped prefix of the registered
24-seed registry. Every source job completed 340 classical evaluations,
and the original artifact SHA-256 plus accepted candidate SHA3-256,
NL/DU/LAT/ANF degree/SAC have been independently checked using the
original GitHub ZIP bytes and a standalone standard-library evaluator.

| Seed | Result | Exact classical hits | Fallback proposals | Source receipt SHA256 prefix |
|---:|---|---:|---:|---|
| 41003 | accepted | 65 | 0 | `cf2860df0ee2` |
| 41011 | ineligible | 0 | 0 | `cb8d6f5add42` |
| 41017 | accepted | 85 | 0 | `55f9bf54f730` |
| 41027 | ineligible | 0 | 0 | `c9d050693734` |
| 41039 | accepted | 114 | 0 | `cc76f62bff4f` |
| 41047 | ineligible | 0 | 0 | `f4a656a4c646` |
| 41051 | accepted | 137 | 0 | `deb6f26d3a8` |
| 41057 | ineligible | 0 | 0 | `2c742bdcbd6f` |
| 41063 | accepted | 93 | 0 | `83bd409a4ca3` |
| 41071 | ineligible | 0 | 0 | `0084fabb7d9c` |
| 41077 | accepted | 106 | 0 | `8b6b12271444` |
| 41081 | accepted | 36 | 0 | `38cfa6f5e68a` |
| 41089 | accepted | 6 | 3 | `7b86b5f9d808` |
| 41101 | ineligible | 0 | 0 | `0fead96648c2` |
| 41113 | accepted | 96 | 0 | `3b15fb1bf245` |
| 41117 | ineligible | 0 | **7** | `6436424aa577` |
| 41131 | accepted | 123 | 0 | `890d83a8f24b` |

## Summary and methodological safeguards

- **17 completed seeds**, 10 selected admissible candidates,
  seven valid ineligible source outcomes.
- **5,780** total classical evaluations; **10** random-swap fallback
  proposals over the 17 source jobs (three in 41089, seven in 41117).
- **ZERO** neural training, neural score inspection or target-scope
  modifications. The first 17 sources cannot yet produce a valid
  12-candidate prediction receipt.
- Each of ten accepted 256-byte permutations independently has
  **NL=100, DU=8, max|LAT|=56, algebraic degree=7**, and SAC within
  the same frozen bound; all ten fingerprints and raw receipt digests
  match the original ZIP source data.
- The ten S-Boxes have distinct full fingerprints and no
  input-XOR/output-XOR relationship **between themselves**. Simple
  clone exclusions against the original six and both v1 sources
  must be applied again on the complete source panel; general affine
  equivalence and independently replayed evolutionary ancestries
  remain unresolved.
- Full source run provenance is NOT proven merely by matching a source
  JSON SHA256. A full deterministic replay of each source-search
  trajectory is a separate audit gate.
- Phase 0, Phase 1 and Phase 2U checks succeeded at the previously
  inspected research head `66bb57d1703c8fa0b4e832697f8510099dcbd3e6`.
  Later changes require their own completed exact-commit CI.

Batch E [GitHub run 41443720643](https://github.com/Chatnoir01/ml/actions/runs/41443720643)
provided the four newer archived source receipts. Next
**strictly ordered** seeds `41141` and `41143` are launched in
the separate Batch F workflow, and cannot push the success count
above the intended maximum of twelve.

**Do not start neural training or freeze a prediction until twelve
source candidates and the complete prefix pass the new admission
gate, with the results documented and independently reviewed.**
