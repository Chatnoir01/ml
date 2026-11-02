# Phase 2U — Nine-source classical audit checkpoint (2 November 2026)

**Research-only.** These are source-candidate outcomes, NOT prospective neural
distinguishing predictions or any proof of production cipher security.
Source version remains `phase2u_source_v1`, with the original frozen 24-seed
prefix, 340 classical evaluations per seed, exact NL/DU/LAT/degree match,
and zero neural trainings.

## Nine consecutive registered source seeds — completed and audited

| Seed | Status | Exact-metric matches in 340-evaluation ledger | Retained fingerprint prefix | Selected SAC | ZIP artifact ID |
|---:|---|---:|---|---:|---:|
| 41003 | accepted | 65 | 00838a3d6db6 | 0.5009765625 | 13113599556 |
| 41011 | ineligible | 0 | — | — | 13136426780 |
| 41017 | accepted | 85 | 011c1ff370ba | 0.500732421875 | 13134649849 |
| 41027 | ineligible | 0 | — | — | 13136142649 |
| 41039 | accepted | 114 | 067c790112b2 | 0.499755859375 | 13136730329 |
| 41047 | ineligible | 0 | — | — | 13135489405 |
| 41051 | accepted | 137 | 018db64035d2 | 0.49951171875 | 13137865391 |
| 41057 | ineligible | 0 | — | — | 13137606727 |
| 41063 | accepted | 93 | 02e0905bcd2e | 0.5000000000 | 13137216809 |

Summary: **9/9 source jobs completed normally, 5 accepted selected
S-Boxes and 4 ineligible sources; 0 neural trainings; 0 bounded fallback
proposals in these nine source runs.**

Accepted candidate properties were recalculated independently from
256-byte permutations using fresh standard-library implementations of:
- Every nonzero input-difference DDT row and global maximum **DU=8**.
- 255 component Walsh-Hadamard transforms and maximum **|LAT|=56**.
- Vectorial component nonlinearity **NL=100**.
- Algebraic normal form by Möbius transform and maximum **degree=7**.
- SAC via the 8 unit input differences, matching the frozen allowed range.
- Candidate SHA3-256 fingerprints and source receipt SHA-256 hashes.

The five selected candidates have five distinct full SHA3 fingerprints,
and no two are input-XOR/output-XOR shifted copies. A further preliminary
DDT-row signature comparison with the six historical Phase 2A and two
prior v1 candidates found no match, but **full general affine equivalence
or independent evolutionary genealogy was NOT established**. This is not
yet the final 12-candidate admission verdict.

Source ZIPs are retained by GitHub Actions and exported to a separate
local archive with SHA256 checksums. The research source code for
independent reproduction is `scripts/phase2u_independent_audit.py`.
The source itself is not privileged evidence: original GitHub ZIPs,
full source-code SHA and an independent re-execution of generation
remain provenance requirements.

## CI issue and resolution

A recent full Phase 0 run failed at **test collection** with
`ModuleNotFoundError: No module named 'scripts'`. The independent
auditor was authored as a standalone Python file in `scripts/`,
outside the installed package. The test was updated to import it
by its explicit checked-out absolute path via `importlib.util`.
This CI *fix* must still be confirmed on the later exact commit
before claiming all Phase 0 checks green.

## Continuation (no neural training)

The next four registered source seeds **41071, 41077, 41081, 41089**
are safe to evaluate together because 5 already accepted + 4
possible accepts is **at most 9**, below the target of twelve.
Their fixed classical-only batch D was explicitly triggered in
`.github/workflows/phase2u-batch-d.yml`. Interpret its source
results only when the original artifacts are available and pass
the same independent audit.

For later seeds, stop on the twelfth accepted candidate **in
registered order**. Do not execute or count later source candidates
past that stopping point; do not select based on neural labels.

**No complete 12-S-Box panel; no frozen prediction; no neural outcome;
no scientific prediction finding; no new cipher security guarantee.**
