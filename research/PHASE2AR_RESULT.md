# Phase 2A-R — Neural Rank-Instability Decomposition Result

## Verdict

**`phase2ar_inconclusive_signal`**

Phase 2A-R does not localize the Phase-2A rank-instability failure to architecture/representation, round count, or input-difference family under its preregistered diagnostic rules.

The result is diagnostic only. It does not qualify a Neural Oracle and does not authorize GA↔NN feedback. Phase 2B remains blocked.

## Frozen execution provenance

- scientific execution SHA: `3edf340537e150fb7733ed03b9fc08cb0c056062`
- GitHub Actions run: `33995098112`
- aggregate artifact ID: `9977815105`
- aggregate artifact ZIP SHA-256: `6d68526ca89325ca2c4c45b58ee5f1457860356375259ebfdce8dd49d65bfc2a`
- aggregate payload SHA-256: `9307bb1c1db815481f178101d59a1acc55e48336f5c3309460fef872956409dc`
- frozen panel digest: `35898535a0df0cfe64431e5f0b6142115d40e3dbeed4a973faa9ba70b1028a30`
- total neural trainings: `240`
- exact training count: `true`
- panel revalidated: `true`
- deterministic receipts: `true`
- neural evolutionary pressure: `false`

The aggregate was computed twice from the same eight cell artifacts and the two JSON outputs were byte-identical before the official result was recorded.

## Adjacent rank correlations

Frozen stability threshold: Spearman rho >= `0.60`.

| Transition | Controlled change | Spearman rho | Nominal rank stability |
| --- | --- | ---: | --- |
| A -> B | architecture/representation bundle | `0.8285714285714286` | stable |
| B -> C | round count 4 -> 5 | `0.8285714285714286` | stable |
| C -> D | input-difference family | `0.6571428571428571` | stable |

These correlations are descriptive because the preregistered signal prerequisites did not pass in all four regimes.

## Per-regime signal checks

### Regime A — bit ReLU MLP, 4 rounds, small-difference family

- heterogeneity permutation p: `0.00009999000099990002` — PASS
- candidate score range: `0.08768214420483517` — PASS
- signal condition: `true` — PASS
- all regime prerequisites: **PASS**

Candidate mean neural advantages in frozen panel order:
`[0.37675103311986896, 0.2960978370837309, 0.3517533942135942, 0.3385856377351465, 0.37393270649535115, 0.38377998128856605]`

### Regime B — byte tanh MLP, 4 rounds, same small-difference family

- heterogeneity permutation p: `0.00009999000099990002` — PASS
- candidate score range: `0.1068102754009217` — PASS
- signal condition: `true` — PASS
- all regime prerequisites: **PASS**

Candidate mean neural advantages:
`[0.3729728043876933, 0.2661625289867716, 0.3273211500721553, 0.2990862182674688, 0.34675564495283584, 0.3396461546241328]`

### Regime C — byte tanh MLP, 5 rounds, same small-difference family

- heterogeneity permutation p: `0.08949105089491051` — **FAIL** (`p >= 0.05`)
- candidate score range: `0.031199719770725373` — PASS
- signal condition: `true` — PASS
- all regime prerequisites: **FAIL**

Candidate mean neural advantages:
`[0.05597521307604336, 0.03706552499501792, 0.03993452420193011, 0.03931740378540177, 0.06826524476574329, 0.06094187813962566]`

### Regime D — byte tanh MLP, 5 rounds, challenger difference family

- heterogeneity permutation p: `0.6788321167883211` — **FAIL** (`p >= 0.05`)
- candidate score range: `0.018920599076915158` — PASS
- signal condition: `true` — PASS
- all regime prerequisites: **FAIL**

Candidate mean neural advantages:
`[0.05480934490721136, 0.04109575659263394, 0.048321996045384806, 0.0358887458302962, 0.05232247606257068, 0.04729886436771269]`

## Interpretation

Phase 2A-R changes the picture from Phase 2A in an important but limited way.

With fresh paired neural seeds, the adjacent candidate rankings are nominally stable across all three controlled transitions: architecture/representation, 4-to-5 rounds, and the input-difference-family change. Therefore the severe Phase-2A cross-regime disagreement (`rho = -0.085714...`) is **not reproduced as a simple deterministic break at one adjacent transition** in this diagnostic.

However, the S-box-specific heterogeneity signal weakens substantially after the move to 5 rounds. Regimes A and B have highly significant between-S-box heterogeneity, while C does not meet the frozen `p < 0.05` requirement and D is clearly non-significant. Because the protocol required all four regimes to carry sufficient signal before interpreting rank transitions, the official result must remain **inconclusive** rather than `phase2ar_no_adjacent_instability` or a localized-transition verdict.

A cautious working hypothesis suggested by these data is that the 5-round regime reduces the strength/reliability of the S-box-specific neural separation enough that rank estimates become seed-sensitive. This is a follow-up hypothesis only, not a confirmed causal conclusion.

## What this does not establish

This result does not establish:
- a stable Neural Oracle;
- neural resistance;
- cryptographic security;
- superiority to AES or another deployed primitive;
- physical side-channel resistance;
- a weakness in a deployed cipher;
- successful GA↔NN co-evolution.

## Frozen next-step rule

Do not retune Phase 2A-R in place and do not feed these scores into the GA.

Any next experiment should be separately preregistered and should test the new uncertainty directly: whether S-box-specific neural heterogeneity/ranking remains stable as round depth increases, using fresh neural seeds and an appropriately frozen replication design. A future oracle qualification still requires its own fresh confirmation before Phase 2B may start.
