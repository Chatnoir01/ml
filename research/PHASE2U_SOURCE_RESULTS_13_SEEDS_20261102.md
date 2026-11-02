# Phase 2U — Independent audit of the first thirteen registered source seeds

**Checkpoint: 2026-11-02. Classical-only source results, not neural findings.**
All results below are drawn from the original GitHub Actions raw source ZIPs,
with independent standard-library recalculation of candidate NL, DU, Walsh
maximum, algebraic degree, SAC, SHA3-256 and JSON source receipt SHA-256.
The frozen source version is `phase2u_source_v1`.

| Ordered source seed | Status | Exact-metric hits in evaluated ledger | Random-swap fallback proposals | Source artifact ID |
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
| 41089 | accepted | 6 | **3** | 13140388590 |

**Summary:** 13 completed source jobs, 8 selected accepted S-Boxes,
5 ineligible source runs, no source failures, 0 neural trainings.
All 13 source receipt JSON SHA-256 values matched their canonical contents.
The accepted eight S-Boxes have the exact frozen global classical metrics:
`NL=100, DU=8, maximum absolute LAT=56, algebraic degree=7`, and
their declared SAC values were independently recomputed. Pairwise exhaustive
input-XOR/output-XOR clone checks found no matches **among those eight**.
Full algebraic/affine family equivalence and source lineage independence
remain unproven.

## First *observed real* bounded-fallback participation

Source seed **41089** successfully produced 340 full classical evaluations,
including **3** proposals from the explicit bounded random-swap fallback.
Its source receipt is valid, and it selected one admissible S-Box.
This supports the statement that the fallback mechanism was used in a
successfully completed live source run. It does NOT demonstrate that the
selected candidate was itself produced by fallback, or that the fallback
was necessary for success. The raw proposal-transcript hash is recorded;
full causal lineage replay requires a separate experiment.

## Source selection discipline

- Exactly **one** candidate per accepted seed counts toward the goal of 12.
  The `65/85/114/137/93/106/36/6` exact-metric counts are NOT independent
  candidate samples or neural observations.
- The first 13 registered source seeds are a contiguous completed prefix.
- Next four preregistered sources `41101, 41113, 41117, 41131` were
  explicitly triggered after this checkpoint. Even four successes would
  reach exactly 12, without exceeding the stopping rule.
- Never choose candidates according to a neural score. No new neural data
  were generated and no classical ranking was frozen from an incomplete panel.
- A full 12-candidate source-panel admission must re-evaluate the raw
  S-Boxes against all eight observed historical and v1 exclusions
  and pairwise candidate equivalences, and the original 340-evaluation
  seed runs should be independently replayed.

Source runs:
- [Pilot](https://github.com/Chatnoir01/ml/actions/runs/41380370307)
- [Batch B](https://github.com/Chatnoir01/ml/actions/runs/41435231175)
- [Batch C](https://github.com/Chatnoir01/ml/actions/runs/41435563912)
- [Batch D](https://github.com/Chatnoir01/ml/actions/runs/41442954695)
- [Batch E (ongoing at checkpoint)](https://github.com/Chatnoir01/ml/actions/runs/41443720643)

## CI status caveat

The independent audit regression was added under `tests/` and initially
broke full Phase 0 collection because the standalone script was imported
as an installed `scripts` package. Commit `28f3ed9714cadade0ac9e6f9d413ad83369643c1`
changed the test to load the script by its checked-out path. Subsequent
exact-head full Phase 0 results were not complete at this checkpoint.
Do NOT label the Phase 0 suite green without the actual GitHub conclusion.

**No validated prospective neural prediction or new real-world cipher claim.**
