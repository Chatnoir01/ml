# Phase 2C-A — Frozen Oracle-pressure diagnostic result

## Status

**FROZEN / VALID ARTIFACT-ONLY DIAGNOSTIC / ARTIFACTS INSUFFICIENT FOR CAUSAL TRACE**

Official classification:

`phase2c_artifacts_insufficient`

Phase 2C-A did not rerun Phase 2B, retrain the Neural Oracle, generate new candidates, evolve a population, or score Block V. It analyzed only the already-frozen Phase 2B arm artifacts.

## Governance and provenance

- Phase 2C preregistration: issue #103
- Phase 2C-A execution lock: issue #104
- Pull request: #105
- Phase 2B scientific source SHA: `59066ad943fc85f24a21b4c2941cbcee4d23aeae`
- Phase 2B workflow run: `34064310593`
- merged Phase 2B source on `main`: `7080f50150dc2feaeb0df7c2193ed880992a39d8`
- Phase 2C-A pre-marker source: `e5b1d7cf93768c1826721dd7e16cfdbe9f3f75ae`
- Phase 2C-A execution marker SHA: `7c6bcc52e8116d77a6bc1e84d8ef53ba1c10358f`
- Phase 2C-A workflow run: `34068279824`
- workflow conclusion: `success`

Before the execution marker, Phase 0 CI was green on Python 3.10, 3.11, and 3.12 and the historical Phase 1 benchmark was green.

The repository-controlled workflow then downloaded the exact frozen Phase 2B artifacts, required the exact 27 arm/seed cells, froze their GitHub artifact metadata and digests, analyzed the cells twice in opposite file order, required byte identity, and uploaded the resulting receipts.

## Frozen receipts

Official diagnostic payload SHA-256:

`185efeb156ba3c2a75cbe9f27375ec795c15e6dc6db208dfd79931d04596c432`

Official source-artifact manifest payload SHA-256:

`875452613c9a9dca6e119a46b872e628f26223470c3eb9ccc351f97d048cf50c`

Phase 2C-A workflow artifact:

- artifact ID: `9999640372`
- artifact name: `phase2c-a-diagnostics-7c6bcc52e8116d77a6bc1e84d8ef53ba1c10358f`
- artifact ZIP SHA-256: `dcafb6e76c28bbe59f19412f0f1b07f3c02617d6e7b9092dbb85e5510835a144`
- files: `phase2c-result.json`, `phase2c-source-artifacts.json`
- source arm-artifact count: `27`
- source workflow run: `34064310593`
- source scientific SHA: `59066ad943fc85f24a21b4c2941cbcee4d23aeae`

Committed machine-readable receipts:

- `research/phase2c-result.json`
- `research/phase2c-source-artifacts.json`

## What Phase 2C-A can measure

Across the nine Oracle cells:

| Diagnostic | Oracle arm |
| --- | ---: |
| cutoff-tie events recorded | 35 |
| shortlist-cutoff tie events | 20 |
| survival-cutoff tie events | 15 |
| tie events whose within-group order changed | 34 |
| budget-close events | 9 |
| candidate scores used during selection | 240 |
| candidate scores used only as terminal audit padding | 48 |
| mean fraction of the 32-score budget used during selection | 0.8333333333333334 |

For comparison, the control recorded 37 cutoff-tie events and used 239/288 candidate scores in selection roles; the shuffled control recorded 31 tie events and used 221/288 candidate scores in selection roles.

Therefore the frozen evidence does **not** support the simple explanation that the Oracle was effectively absent. In the Oracle arm, recorded score-based ordering differed from the historical classical base order in 34 of 35 recorded tie events, and 240 of 288 candidate scores across the nine seeds were consumed before terminal audit padding.

Every Oracle seed also reached the frozen selection-budget closure condition once. One particularly restrictive cell was seed `326071`: only 9 candidate scores had participated in selection when a boundary group of size 24 arrived with 23 score slots remaining, so the no-partial-group rule closed further Oracle selection pressure for that cell.

## What the frozen Phase 2B schema cannot establish

The Phase 2B tie-event payload does not record these fields:

- `generation`
- `group_start`
- `group_end`
- `selected_before`
- `selected_after`

It also contains no cross-generation lineage or terminal ancestry identifier.

Therefore Phase 2C-A cannot validly reconstruct:

- complete opportunity density after selection-budget closure;
- exact candidate membership flips at each cutoff;
- the generation in which each intervention occurred;
- 1/2/5-generation persistence of an intervention;
- descendant survival to terminal selection;
- whether the final Phase-1O terminal rule erased a specific earlier Oracle-caused change.

Those facts cannot be recovered by assumption from final outcomes.

## Additional frozen artifact-level observation

A read-only comparison of the already-frozen Phase 2B arm artifacts, without using Block V, shows that the Oracle arm's `proposal_audit_sha256` and terminal fingerprint differ from the matched classical control on 8 of 9 evolution seeds:

`326011, 326023, 326033, 326047, 326051, 326063, 326071, 326099`

On seed `326087`, both the proposal-audit digest and terminal fingerprint remain identical to control even though the Oracle artifact contains five recorded tie events whose within-group ordering changed.

This establishes that Oracle-associated ordering was capable of changing the downstream trajectory on most seeds, while at least one seed demonstrates that recorded reordering need not alter the eventual proposal trace or terminal candidate. It still does **not** identify the exact cutoff membership transition or causal lineage because the required event fields were not recorded.

## Frozen interpretation

The correct Phase 2C-A classification is therefore:

`phase2c_artifacts_insufficient`

This classification does **not** mean that Phase 2B had no Oracle pressure. The evidence instead shows substantial recorded Oracle reordering and substantial selection-budget use, but the Phase 2B receipt schema is too coarse to distinguish among the preregistered causal explanations about cutoff membership, persistence, and terminal erasure.

Phase 2B remains unchanged as the valid negative held-out result `phase2b_oracle_pressure_not_supported`.

## Logical successor

The next justified step is a separately preregistered **Phase 2C-B deterministic instrumented replay**, not a new optimizer and not full GA↔NN co-evolution.

A valid Phase 2C-B should:

- use the frozen Phase 2B evolution seeds and classical engine;
- use already-frozen Phase 2B Oracle scores as a read-only score cache where exact replay permits it;
- perform **zero new neural training** and **zero Block-V scoring**;
- first prove exact replay identity against each original arm's `proposal_audit_sha256` and terminal fingerprint;
- record generation, selection stage, exact group start/end around the cutoff, selected membership before/after, candidates entering/leaving selection, parent/proposal ancestry, and terminal ancestry;
- continue recording opportunity groups even after the 32-score selection budget closes, without allowing them to affect evolution;
- treat any inability to reproduce Phase 2B exactly as a replay/provenance failure rather than modifying the historical result.

Only after that diagnostic replay is frozen should a new Phase 2D optimization mechanism be designed, with its own preregistration and fresh held-out neural validation seeds.

## Scope

Educational/defensive ToySPN research only. No claim about AES or any deployed cipher, no operational key recovery, and no adaptive GA↔NN co-evolution is made or authorized by Phase 2C-A.
