# Neural residual screen — frozen 100-training result

## Verdict

The preregistered 100-training exploratory screen completed successfully on frozen experiment SHA:

`3df5798a5e8b934435f61923d71ab63171ad4641`

Workflow run:

`33579798498`

Aggregate evidence artifact:

- artifact ID: `9827993929`
- digest: `sha256:ad626b88201b7ca9bd1a328ba2479168d5a4dbfe36776f31ffee4acc562169a0`

All ten candidate jobs completed successfully: 10 classically matched S-boxes × 10 paired replicates = **100 neural trainings**.

The preregistered diagnostic is:

`residual_signal_no_heterogeneity`

Global Gate 1 remains RED. The neural oracle remains blocked.

## Frozen panel

Every candidate was revalidated by the workflow preflight before training and matched exactly:

- nonlinearity: `100`
- differential uniformity: `8`
- maximum linear correlation: `56`
- algebraic degree: `7`
- SAC: `0.5`

The panel and all data/model seeds were committed before any AUC was produced.

## Aggregate result

Across the ten candidate means:

- mean neural advantage averaged across candidates: `0.05932903917195826`
- mean null advantage averaged across candidates: `0.023347418414098254`
- mean test AUC averaged across candidate means: `0.5292596945775498`
- candidate mean advantage range: `0.030968658590070877`
- heterogeneity statistic (variance of candidate mean advantages): `9.352521399646501e-05`
- paired within-replicate permutation p-value, 5000 permutations: `0.3525294941011798`

The largest candidate mean neural advantage was candidate `1`:

- fingerprint: `0d8e178cb452db1edf2668dd4848705696c659d29cc7e53ef0a3190b49db01c1`
- mean test AUC: `0.5367151967409909`
- mean neural advantage: `0.0734303934819818`
- mean null advantage: `0.027499777758164146`
- median neural advantage: `0.0819113095580416`
- within-candidate standard deviation of advantage: `0.03530904397277377`

The smallest candidate mean neural advantage was candidate `5`:

- fingerprint: `4495c13476d491d7317800533ad447946fa918f05c09ab5c36be206337252c2b`
- mean test AUC: `0.5212308674459555`
- mean neural advantage: `0.04246173489191092`
- mean null advantage: `0.01770013899707341`

## Per-candidate means

| candidate | mean AUC | mean advantage | mean null advantage |
|---:|---:|---:|---:|
| 0 | 0.5287807197638351 | 0.057561439527670274 | 0.01897954228656181 |
| 1 | 0.5367151967409909 | 0.0734303934819818 | 0.027499777758164146 |
| 2 | 0.5357667598557417 | 0.07153351971148343 | 0.030219450761886767 |
| 3 | 0.5288880088659760 | 0.05777601773195211 | 0.02688255635972141 |
| 4 | 0.5340279393141303 | 0.06805587862826043 | 0.020607521583518706 |
| 5 | 0.5212308674459555 | 0.04246173489191092 | 0.01770013899707341 |
| 6 | 0.5258051329261495 | 0.05161026585229909 | 0.026418993240562128 |
| 7 | 0.5330115721194929 | 0.06602314423898567 | 0.020977844419728407 |
| 8 | 0.5278437736161418 | 0.05568754723228353 | 0.024435061499526567 |
| 9 | 0.5205269751270852 | 0.04915045042275534 | 0.019753297234239187 |

## Scientific interpretation

The frozen MLP can exploit a residual reduced-round signal at the tested data/model budget: the strongest matched candidate passes the preregistered signal-vs-null conditions.

However, the paired heterogeneity test does **not** support the claim that the signal differs reproducibly between these ten classically matched S-boxes (`p=0.3525`). The observed numerical range in mean advantage is therefore not sufficient evidence of an S-box-specific neural fitness landscape.

The most conservative interpretation is that the current neural signal is substantially shared by the fixed ToySPN / round count / input difference / representation, rather than demonstrably controlled by which of these matched Phase-1H S-boxes is used.

Therefore this experiment does **not** justify turning the present MLP score into an evolutionary fitness oracle yet. The next neural diagnostic should increase sensitivity to S-box-specific structure while preserving matched classical metrics, for example by preregistering a batch over several round counts/input differences and independent challenger architectures. Fresh-population classical transfer is still separately required before Phase 2 can be unblocked.
