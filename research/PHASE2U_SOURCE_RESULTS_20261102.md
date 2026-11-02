# Phase 2U — Original source receipt ledger, 2 November 2026

**Research-only; not a blind prediction confirmation. No Phase 2U neural training.**

This ledger records the initial **six contiguous** publicly registered source seeds
of version `phase2u_source_v1`. Each successful GitHub Actions job executed
exactly 340 classical candidate evaluations, including 320 guided proposals
and 20 initial entries. None invoked the fallback; absence of fallback use
does **not** validate the fallback under real long-term failure schedules.

| Seed | Raw source status | Exact-metric hits in evaluated ledger | Chosen S-Box fingerprint (prefix) | Source SHA256 (prefix) | GitHub ZIP artifact ID |
|---:|---|---:|---|---|---:|
| 41003 | accepted | 65 | `00838a3d6db6` | `cf2860df0ee2` | 13113599556 |
| 41011 | ineligible | 0 | — | `cb8d6f5add42` | 13136426780 |
| 41017 | accepted | 85 | `011c1ff370ba` | `55f9bf54f730` | 13134649849 |
| 41027 | ineligible | 0 | — | `c9d050693734` | 13136142649 |
| 41039 | accepted | 114 | `067c790112b2` | `cc76f62bff4f` | 13136730329 |
| 41047 | ineligible | 0 | — | `f4a656a4c646` | 13135489405 |

All six original artifact ZIP files were retrieved through the GitHub connector.
The private local independent auditor checked the original source payload SHA256,
byte permutation validity, exact independent S-Box SHA3 fingerprints,
and recomputed the full DDT maxima, Walsh maximum, algebraic degree and SAC
for accepted candidates WITHOUT calling the repository's classical evaluator.

### Independent mathematical recomputation of the three accepted candidates

| Seed | NL | DU | max LAT | degree | SAC |
|---:|---:|---:|---:|---:|---:|
| 41003 | 100 | 8 | 56 | 7 | 0.5009765625 |
| 41017 | 100 | 8 | 56 | 7 | 0.500732421875 |
| 41039 | 100 | 8 | 56 | 7 | 0.499755859375 |

The accepted candidates have distinct SHA3-256 fingerprints and are NOT
simple input-XOR/output-XOR clones of one another. For the DDT row at
input difference 0x01, their sum of squared output counts is respectively
696, 864 and 776, different from each of the six historical Phase 2A
candidates (720, 728, 752, 744, 832 and 736) and the two Phase 2T-v1
accepted candidates (728 and 760). Since that DDT row is invariant under
S(x XOR a) XOR b, this also rules out that simple transformation family
against the eight earlier observed S-Boxes.

**Important limitations:**
- The source SHA256 does NOT prove that a generator executed faithfully.
  Independently replaying the complete 340-evaluation process is a
  distinct future provenance gate.
- The local audit and raw ZIP artifacts are separate from the GitHub
  source-panel checker in `src/adversarial_sbox/phase2u_panel.py`.
- The new repo-independent standard-library auditor lives in
  `scripts/phase2u_independent_audit.py`. Its complete CI suite is
  being verified; do not claim those new tests passed until confirmed.
- General linear/affine equivalence and correlated ancestral generation
  are NOT excluded or mathematically ruled out.
- These are **three chosen source candidates, not 65+85+114 independent
  experimental observations**; only the deterministic chosen candidate
  per seed may contribute toward the target panel of twelve.
- The next registered seeds (41051, 41057, 41063) were queued/in progress
  at the time this ledger was written. Their status is NOT included here,
  and no later seeds may be counted as eligible until earlier source
  receipts pass audit.
- No prospective neural results, neural prediction correlations, cipher
  security claim or cryptographic novelty are established here.

### Source runs

- First source seed 41003: https://github.com/Chatnoir01/ml/actions/runs/41380370307
- Four-seed source batch B: https://github.com/Chatnoir01/ml/actions/runs/41435231175
- Next source batch C: https://github.com/Chatnoir01/ml/actions/runs/41435563912

The complete original SHA256 values and 256-byte permutations remain
inside the respective raw GitHub source ZIP artifacts. A separately
exported local audit bundle contains the six original JSON receipts,
their unaltered byte hashes, mathematical recomputation and a manifest.
GitHub Actions artifact retention is limited; original ZIPs should be
retained separately if required for long-term research provenance.
