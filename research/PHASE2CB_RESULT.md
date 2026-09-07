# Phase 2C-B — Frozen deterministic instrumented replay result

## Status

**FROZEN / VALID 27-CELL DETERMINISTIC REPLAY / TRANSIENT ORACLE MEMBERSHIP EFFECTS OBSERVED**

Official replay status:

`phase2cb_replay_valid`

Phase 2C-B did not create a new optimizer, retrain the Neural Oracle, rescore Block V, change any Phase 2B seed/budget/threshold, or authorize adaptive GA↔NN co-evolution. It deterministically replayed the exact frozen Phase 2B arm semantics using only the already-recorded score receipts.

## Governance and provenance

- Phase 2C-B preregistration: issue #106
- Phase 2C-B execution lock: issue #107
- Pull request: #108
- Phase 2C-A merged source: `fc66ac5d5dde2763d64873cf794d6a2b18e122fa`
- Phase 2C-B pre-marker source: `6a38c9b42518ccd916a0c796d789595f755b343f`
- Phase 2C-B execution marker: `d103cd797f54e5bab5f971acf7bbe210204a623a`
- exact authorization token: `AUTHORIZED_PHASE2CB_FROZEN_SCORE_REPLAY`
- Phase 2B scientific source SHA: `59066ad943fc85f24a21b4c2941cbcee4d23aeae`
- Phase 2B workflow run: `34064310593`
- Phase 2C-B workflow run: `34074106557`
- workflow conclusion: `success`

Before the execution marker, Phase 0 CI was green on Python 3.10, 3.11 and 3.12 on the exact pre-marker source and the historical Phase 1 benchmark was green. The branch diff before authorization contained only new Phase 2C-B protocol/replay/runner/CLI/workflow/test files and did not modify frozen Phase 2B results, seed registries, budgets, validation blocks, Oracle datasets or thresholds.

The execution workflow installed the package without neural extras, statically rejected neural scorer / Block-V import paths, downloaded the exact 27 frozen Phase 2B arm artifacts, verified the Phase 2C-A source-artifact manifest byte-for-byte, then replayed all 27 cells twice from opposite input ordering and required byte-identical aggregate output.

## Frozen receipts

Official replay aggregate SHA-256:

`ecff17f429589d6f0b4031f38c5a18be7843c684e993dff0a3258124e692b0cc`

Source-artifact manifest payload SHA-256:

`875452613c9a9dca6e119a46b872e628f26223470c3eb9ccc351f97d048cf50c`

Official Phase 2C-B workflow artifact:

- artifact ID: `10003757350`
- artifact name: `phase2cb-replay-d103cd797f54e5bab5f971acf7bbe210204a623a`
- artifact ZIP SHA-256: `e8e24ca0142433d50cbc77d339ffe8b66a806e6e4254e7f887bf140cccbd995a`
- artifact size: `1215156` bytes
- created: `2026-09-07T03:55:24Z`
- expires: `2026-12-06T01:46:40Z`
- files: full `phase2cb-result.json` and `phase2cb-source-artifacts.json`

The full replay JSON is approximately 13.7 MB uncompressed because it contains generation-by-generation fingerprints, cutoff traces and parent maps. The repository therefore freezes a compact machine-readable summary plus the exact source manifest, while the full detailed machine receipt remains preserved in the GitHub Actions artifact above and is bound by its SHA-256 digest.

Committed receipts:

- `research/phase2cb-result-summary.json`
- `research/phase2cb-source-artifacts.json`
- `research/PHASE2CB_RESULT.md`

## Replay identity gate

All **27/27** arm/seed cells passed every preregistered replay identity gate.

For each cell, the replay exactly matched the frozen Phase 2B record on:

1. initial population digest;
2. classical evaluation count;
3. historical selection-role frozen-score fingerprint sequence;
4. legacy Oracle event projection;
5. proposal audit SHA-256;
6. terminal fingerprint;
7. terminal S-Box;
8. terminal classical metrics;
9. Oracle selection-closed state.

There were no replay provenance failures.

Execution receipts:

- `cell_count = 27`
- `identity_pass_count = 27`
- `instrumented_replay_runs = 27`
- `new_neural_trainings = 0`
- `block_v_scores = 0`

The second complete traversal produced byte-identical output to the first traversal.

## Boundary opportunity and membership results

The replay resolves the key ambiguity left by Phase 2C-A: Oracle ordering did not merely reshuffle candidates harmlessly inside exact protected-key groups. It repeatedly changed which candidates crossed the actual selection boundary.

| Arm | Boundary opportunities | Pre-closure | Post-closure | Membership flips | Ordering-only events | Budget-block events |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Control | 359 | 46 | 313 | 0 | 0 | 9 |
| Oracle | 362 | 44 | 318 | 31 | 3 | 9 |
| Shuffled | 360 | 40 | 320 | 31 | 0 | 9 |

For the Oracle arm specifically:

- 31 real membership-flip events occurred;
- 17 occurred at the shortlist cutoff;
- 14 occurred at the survival cutoff;
- 3 additional scored events changed ordering without changing membership;
- every one of the 9 evolution seeds had at least one Oracle membership flip;
- every Oracle seed also reached the frozen no-partial-group budget closure once;
- 318 additional exact-key boundary opportunities were observed after closure, but were observational-only and could not affect evolution.

Per-seed Oracle membership flips were:

| Evolution seed | Pre-closure opportunities | Membership flips | Ordering-only | Post-closure opportunities |
| ---: | ---: | ---: | ---: | ---: |
| 326011 | 5 | 4 | 0 | 35 |
| 326023 | 5 | 4 | 0 | 35 |
| 326033 | 5 | 3 | 1 | 36 |
| 326047 | 5 | 4 | 0 | 36 |
| 326051 | 5 | 4 | 0 | 35 |
| 326063 | 5 | 4 | 0 | 35 |
| 326071 | 3 | 1 | 0 | 37 |
| 326087 | 6 | 4 | 1 | 33 |
| 326099 | 5 | 3 | 1 | 36 |

This directly rejects the simple explanation that Phase 2B failed merely because the Oracle never changed actual cutoff membership.

## Persistence and lineage of Oracle-entered candidates

Across the 31 Oracle membership-flip events, the replay recorded 81 entered-candidate occurrences corresponding to 64 unique candidate fingerprints.

Using the unique fingerprints and taking the logical OR across repeated appearances:

| Persistence diagnostic | Unique Oracle-entered fingerprints |
| --- | ---: |
| Directly present at +1 generation | 43 / 64 |
| Directly present at +2 generations | 0 / 64 |
| Directly present at +5 generations | 0 / 64 |
| Has any descendant at +1 generation | 12 / 64 |
| Has any descendant at +2 generations | 2 / 64 |
| Has any descendant at +5 generations | 0 / 64 |
| Is the terminal candidate | 0 / 64 |
| Has the terminal candidate as a descendant | 0 / 64 |

This is the strongest new mechanistic observation from Phase 2C-B.

Oracle-caused membership changes were real and common, but the replayed lineages were short-lived. Many entered candidates survived directly to the next generation, a smaller subset generated descendants one generation later, only two unique entered candidates still had any descendant at +2, and none had a tracked descendant at +5 or at the terminal candidate.

Therefore the frozen evidence is consistent with **transient trajectory perturbation followed by rapid lineage extinction / classical replacement**, rather than with an Oracle effect that propagates to the terminal selection.

This is a descriptive statement about the frozen ToySPN replay. It is not a claim that a particular later selection operator is uniquely causal, and it does not retroactively change the Phase 2B held-out result.

## Shuffled-control specificity

An important negative-control fact must be preserved: the shuffled-score arm also produced **31 membership flips**.

Therefore Phase 2C-B does **not** establish that the mere number of membership flips is Oracle-specific or sufficient to create held-out neural improvement. The Oracle arm produced 31 flips from 44 pre-closure opportunities, while shuffled produced 31 flips from 40 pre-closure opportunities.

This prevents the outcome-driven claim that “more membership changes” by itself explains or rescues the Oracle hypothesis. The distinguishing information for any future mechanism study must concern the *quality, direction, persistence or protected integration* of those changes, not simply their count.

## Relationship to Phase 2B and Phase 2C-A

Phase 2B remains frozen as the valid negative held-out result:

`phase2b_oracle_pressure_not_supported`

Phase 2C-A remains frozen as:

`phase2c_artifacts_insufficient`

Phase 2C-B resolves the specific missing instrumentation that caused the 2C-A insufficiency:

- exact generations are now known;
- exact cutoff-boundary groups are known;
- selected membership before/after is known;
- entered/exited candidates are known;
- proposal parentage is known;
- lineage persistence is known;
- terminal ancestry is known.

The replay shows that Oracle pressure was materially active at real selection boundaries, but the induced changes did not persist to the terminal candidate under this frozen Phase 2B mechanism.

## Frozen interpretation

The correct scientific interpretation after Phase 2C-B is:

1. **Replay provenance is valid.** The 27 original Phase 2B trajectories were reproduced exactly under frozen-score replay.
2. **Oracle pressure was materially active.** It caused 31 actual membership flips across all nine seeds.
3. **The pressure was budget-limited.** Most recorded boundary opportunities occurred after the frozen selection-score budget had already closed and were observational-only.
4. **The membership effect was short-lived.** No Oracle-entered candidate or tracked descendant survived to +5 or terminal ancestry.
5. **Membership-flip count is not Oracle-specific.** The shuffled negative control also produced 31 flips.
6. **Phase 2B remains unsupported.** Phase 2C-B explains mechanism behavior; it does not convert the negative held-out Phase 2B result into support.

## Logical successor

The next scientific step should **not** be an automatic full adaptive GA↔NN co-evolution run.

A future Phase 2D may now be designed, but only under a new preregistration and fresh held-out neural validation seeds. The design question is no longer “did the Oracle ever change selection?” Phase 2C-B answered that: yes.

The justified next question is whether a newly preregistered mechanism can preserve a neural signal long enough to matter **without degrading the protected classical security key**, while also demonstrating specificity beyond the shuffled control.

Any Phase 2D candidate mechanism must therefore declare ex ante:

- how Oracle influence is allowed to persist beyond one generation;
- how classical non-degradation remains absolute;
- how score-budget exposure is controlled;
- how shuffled/random-score specificity will be tested;
- fresh fitness/validation separation and fresh held-out validation seeds;
- success thresholds before execution;
- no reuse of Phase 2B Block-V outcomes for tuning.

A conservative option is to preregister a bounded persistence mechanism or Pareto-style protected secondary objective rather than jump directly to fully adaptive bidirectional GA↔NN co-evolution.

## Scope

Educational/defensive ToySPN research only. No AES or deployed-cipher claim, no operational key-recovery claim, no side-channel claim, and no adaptive attack deployment is made or authorized by Phase 2C-B.
