# Phase 2B — Frozen scientific result

## Status

**FROZEN / VALID / ORACLE PRESSURE NOT SUPPORTED**

Official verdict:

`phase2b_oracle_pressure_not_supported`

This is a valid negative scientific result, not a provenance or execution failure. The qualified Phase 2A-U2 Neural Oracle remains a valid measurement procedure, but the preregistered Phase 2B one-way GA ← frozen Oracle pressure mechanism did not satisfy the held-out support criteria.

Full adaptive GA↔NN co-evolution remains out of scope and was not executed.

## Frozen governance

- Public preregistration: issue #97
- Execution lock: issue #98
- RED-first implementation contract: issue #99
- Ex-ante matched Oracle budget amendment: issue #101
- Sign-test / classical-gate clarification: issue #102
- Pull request: #100
- Pre-marker source SHA: `49f9df6ed9c243ebd81adc77039cfd502515c09b`
- Scientific execution SHA: `59066ad943fc85f24a21b4c2941cbcee4d23aeae`
- Workflow: `Phase 2B GA-Oracle Pressure`
- Workflow run ID: `34064310593`
- Workflow conclusion: `success`

The scientific SHA was frozen before any Phase 2B outcome was observed. No threshold, seed, arm, budget, Oracle regime, endpoint, held-out block, or interpretation rule was changed after execution.

## Execution completion

The run completed the entire preregistered pipeline successfully:

- preflight: GREEN;
- complete regression suite: GREEN;
- historical Phase 1 benchmark replay: GREEN;
- 27/27 arm jobs (3 arms × 9 seeds): GREEN;
- 27/27 terminal held-out Block-V evaluations: GREEN;
- 27/27 arm artifacts uploaded and digest-verified;
- aggregate job: GREEN;
- aggregate generated twice and byte-identical.

## Provenance prerequisites

All aggregate prerequisites passed:

```text
exact_budgets: true
receipt_integrity: true
same_initial_population: true
terminal_validation_identity: true
validation_seed_gate: true
pass: true
```

Protected classical outcome:

`CLASSICAL_NON_DEGRADATION = true`

Therefore this result is interpreted as a valid scientific non-support result rather than `phase2b_inconclusive_prerequisites`.

## Frozen support checks

| Preregistered criterion | Result |
| --- | --- |
| Arm O beats Arm C on at least 8/9 seeds | **FAIL** — 6/9 |
| One-sided exact paired sign test `p < 0.05` | **FAIL** — `p = 0.25390625` |
| Mean paired reduction `(C - O) >= 0.02` | **FAIL** — `-0.0005258649435821007` |
| Classical non-degradation | **PASS** |
| Arm O beats Arm S on at least 6/9 seeds | **FAIL** — 3/9, with 2 ties |
| O reduction vs C strictly exceeds S reduction vs C | **PASS** |

Because all six criteria were required, the frozen verdict is:

`phase2b_oracle_pressure_not_supported`

## Arm O versus Arm C — held-out Block V

- wins: `6`
- losses: `3`
- ties: `0`
- exact one-sided sign-test p-value: `0.25390625`
- mean paired reduction `(C - O)`: `-0.0005258649435821007`

Per-seed reductions in the frozen evolution-seed order
`(326011, 326023, 326033, 326047, 326051, 326063, 326071, 326087, 326099)`:

```text
[-0.0479323133780204,
 -0.031618566700384765,
  0.0021823545006268152,
  0.050320192358945304,
  0.0016806690311667039,
  0.059477333519646236,
 -0.0430979125917888,
  3.495259637276149e-12,
  0.004255458764074738]
```

The negative mean means Arm O was very slightly worse than Arm C on average under the frozen held-out endpoint; it did not approach the preregistered `+0.02` improvement threshold.

## Specificity — Arm O versus shuffled Arm S

- O wins over S: `3`
- ties: `2`
- mean reduction `(C - S)`: `-0.015539942790370001`

Per-seed `(S - O)` held-out differences:

```text
[0.01943876170010944,
 -0.034963717170439335,
 -0.004823568611523943,
 -0.004810816012653485,
  0.0,
  0.05497634844732657,
  0.0,
 -0.02753627000837361,
  0.13284596227664547]
```

The preregistered specificity requirement of at least 6/9 O-over-S wins was not met.

## Receipts

Aggregate scientific payload SHA-256:

`a3f67c1b60b8c1755ce2a55572cf7906c27cb6c7c67e98417b346435b2418699`

Frozen summary artifact:

- artifact ID: `9998715882`
- name: `phase2b-summary-59066ad943fc85f24a21b4c2941cbcee4d23aeae`
- artifact ZIP SHA-256: `6b4adba352884c53afb939e768bf1abc53d90695df543e98d98647e2e3e755cc`
- created: `2026-09-06T22:51:28Z`
- expires: `2026-12-05T22:32:23Z`
- expired at freeze time: `false`

The aggregate downloaded all 27 arm artifacts and verified their recorded SHA-256 digests before classification.

## Interpretation boundary

This result supports only the following statement:

> Under this frozen ToySPN protocol, the specific conservative Phase 2B mechanism that allowed the qualified frozen Neural Oracle to influence selection only inside exact protected-classical-key cutoff ties did not produce the preregistered held-out improvement.

It does **not** show that the Phase 2A-U2 Oracle is invalid, that neural guidance can never help evolutionary S-Box search, or that any deployed cipher is weak or strong. The experiment does not establish why the Phase 2B mechanism failed; explanations such as insufficient tie opportunities or fitness/held-out misalignment remain hypotheses requiring separately preregistered diagnostics.

## No outcome-driven retry

This run must not be rerun with altered seeds, thresholds, budgets, tie rules, Oracle seeds, validation seeds, or post-hoc selection logic to rescue the hypothesis. Any successor experiment must be separately preregistered and must preserve this negative result unchanged.

## Scope

Educational/defensive ToySPN research only. No AES/deployed-cipher claim, operational key recovery claim, or full adaptive GA↔NN co-evolution claim is made by Phase 2B.
