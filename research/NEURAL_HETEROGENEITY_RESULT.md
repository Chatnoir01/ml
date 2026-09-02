# Neural S-box heterogeneity challenger — frozen 1200-training result

## Verdict

The preregistered multi-regime challenger completed successfully on frozen experiment SHA:

`c2cbba63a090ecd20aab8a90fe18b1fbe79e881c`

Workflow run:

`33650462622`

Aggregate evidence artifact:

- artifact ID: `9854610381`
- digest: `sha256:34b9bcf93e24ce68692e767dba49f0338c91907710a1a2f1b4fd7aa1f19674fe`

All 24 matrix cells completed successfully:

- 10 classically matched S-boxes
- 3 round counts
- 4 input differences
- 2 independent neural architectures
- 5 paired replicates

Total: **1200 neural trainings**.

The frozen diagnostic is:

`residual_signal_no_sbox_heterogeneity`

Global Gate 1 remains RED. The neural oracle remains blocked.

## Frozen matched panel

Every S-box was revalidated by workflow preflight before training and matched exactly:

- nonlinearity: `100`
- differential uniformity: `8`
- maximum linear correlation: `56`
- algebraic degree: `7`
- SAC: `0.5`

No S-box, regime, seed, architecture, threshold, or verdict rule was changed after the
experimental SHA was frozen.

## Primary blocked heterogeneity result

The preregistered global blocked test shuffled only S-box identity inside each
`(round count, input difference, architecture, replicate)` block.

Observed aggregate statistics:

- total trainings: `1200`
- global heterogeneity variance: `2.716871387217256e-05`
- global blocked permutation p-value, 10000 permutations: `9.999000099990002e-05`
- range of the ten overall S-box mean neural advantages: `0.014610401765206255`
- preregistered minimum effect-size range: `0.015`
- shortfall from the frozen range threshold: `0.0003895982347937449`

Thus the global permutation evidence is strong, but the preregistered effect-size condition
is not met. The observed range is about 2.6% below the frozen `0.015` threshold. The threshold
is not relaxed post hoc.

## Independent architecture replication

Both architecture-specific blocked tests are significant:

| architecture | heterogeneity variance | permutation p |
|---|---:|---:|
| `bit_relu_mlp` | `2.9042987423543064e-05` | `0.0001999600079984003` |
| `byte_tanh_mlp` | `3.9040652318432586e-05` | `0.0001999600079984003` |

Spearman correlation between the ten architecture-specific S-box mean advantages:

`0.6363636363636364`

This exceeds the frozen replication threshold of `0.40`.

Therefore conditions for architecture-level reproducibility are individually satisfied, but
the final preregistered positive verdict still fails because the global effect-size range is
below `0.015`.

## Strongest overall candidate

Candidate `1` has the largest overall mean neural advantage:

- fingerprint: `0d8e178cb452db1edf2668dd4848705696c659d29cc7e53ef0a3190b49db01c1`
- overall mean neural advantage: `0.2493858819525925`
- overall mean null advantage: `0.024092046438105853`
- median neural advantage: `0.048317593028206596`
- standard deviation across the 120 blocks: `0.3544380354831632`
- `bit_relu_mlp` mean advantage: `0.25233900301845663`
- `byte_tanh_mlp` mean advantage: `0.2464327608867283`

The frozen residual-signal condition is comfortably satisfied.

## Per-candidate aggregate means

| candidate | mean advantage | mean null advantage | bit mean | byte mean |
|---:|---:|---:|---:|---:|
| 0 | `0.24332105302907356` | `0.025072616718247696` | `0.24088530321350035` | `0.2457568028446468` |
| 1 | `0.2493858819525925` | `0.024092046438105853` | `0.25233900301845663` | `0.2464327608867283` |
| 2 | `0.24670216245738066` | `0.02286970141849971` | `0.2501158818063555` | `0.24328844310840542` |
| 3 | `0.23594383029003788` | `0.022926200626126193` | `0.2370599483247632` | `0.23482771225531243` |
| 4 | `0.24430398122342972` | `0.026346516623887938` | `0.24402639732573467` | `0.24458156512112467` |
| 5 | `0.23559818458901588` | `0.02529295564832797` | `0.23900275719338973` | `0.23219361198464197` |
| 6 | `0.24781316364865977` | `0.02865322153129209` | `0.24940881552848634` | `0.2462175117688331` |
| 7 | `0.2463030638394141` | `0.025061880737611522` | `0.24817392808093228` | `0.24443219959789542` |
| 8 | `0.23934850727959095` | `0.02587430330445397` | `0.23711626560059623` | `0.2415807489585858` |
| 9 | `0.23477548018738625` | `0.025030207276539863` | `0.24143000863800393` | `0.22812095173676852` |

## Regime structure

The experiment also shows that signal strength depends very strongly on the reduced-round
regime. In particular, the 3-round single-byte-difference regimes are nearly perfectly
distinguishable for every matched S-box, so they contribute a large shared ToySPN signal
rather than a large between-S-box spread.

Selected regime receipts:

| rounds | input difference | S-box mean-advantage range | maximum mean advantage |
|---:|---:|---:|---:|
| 3 | `0x00000001` | `0.00432181703010881` | `0.9947994632359233` |
| 3 | `0x00000100` | `0.004690854191227056` | `0.9955629093546172` |
| 4 | `0x00000001` | `0.06215516627651563` | `0.36076604151165537` |
| 4 | `0x00000100` | `0.0852846594876897` | `0.38148431007024663` |
| 5 | `0x00000001` | `0.02428344989984345` | `0.05838615323353413` |
| 5 | `0x00000100` | `0.034356218210438494` | `0.06887372468314923` |

This explains why a statistically stable S-box ordering can coexist with an overall
preregistered effect-size range that remains just below the final threshold: much of the
absolute neural advantage is a shared regime effect.

## Frozen criteria audit

The preregistered positive verdict `replicated_sbox_heterogeneity` required all seven
conditions:

1. exactly 1200 trainings with complete provenance — **PASS**
2. global blocked heterogeneity `p < 0.01` — **PASS**
3. global S-box mean-advantage range `>= 0.015` — **FAIL** (`0.014610401765206255`)
4. `bit_relu_mlp` heterogeneity `p < 0.05` — **PASS**
5. `byte_tanh_mlp` heterogeneity `p < 0.05` — **PASS**
6. architecture Spearman `>= 0.40` — **PASS** (`0.6363636363636364`)
7. at least one S-box mean advantage `>= 0.04` and at least `0.02` above null — **PASS**

Because condition 3 fails, the frozen verdict cannot be upgraded to
`replicated_sbox_heterogeneity`.

## Scientific interpretation

This result is substantially stronger than the earlier 100-training screen. Stable S-box
identity now produces a highly significant blocked permutation statistic, the effect appears
separately in two materially different neural representations, and the architecture-specific
S-box rankings have moderate positive agreement.

However, the experiment was explicitly designed with both a significance requirement and a
minimum effect-size requirement. The latter misses by a small but real margin. Therefore the
correct preregistered conclusion is not a positive heterogeneity claim.

The data support the narrower statement that **there is reproducible statistical structure
associated with S-box identity in this reduced-round ToySPN challenge, but the preregistered
minimum global between-S-box effect size was not reached**.

This evidence does not justify enabling the neural score as an evolutionary fitness oracle.
Global Gate 1 remains RED, and fresh-population classical transfer remains separately required
before any later Phase-2-style co-evolution experiment can be scientifically justified.
