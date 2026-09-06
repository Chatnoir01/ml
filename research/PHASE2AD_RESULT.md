# Phase 2A-D — Neural Signal Attenuation with Depth — Result

Status: frozen scientific result. No in-place retuning is permitted.

Public preregistration: issue #62.
Pull request: #63.
Base main commit: `13f8ae0d019d126a15c52896b8bfc49fe6addd0e`.
Scientific execution commit: `cdad9c0fda1eaee181c5dc3cf8d05ffc869762f6`.
Workflow run: `34003260315`.

## Official frozen verdict

**`phase2ad_depth_attenuation_not_supported`**

The preregistered primary 4→5-round attenuation hypothesis is **not supported under the frozen decision rule**. The observed between-S-box variance falls sharply from R4 to R5, but the paired one-sided randomization test does not reach the preregistered `p < 0.05` threshold.

This result is preserved as negative. No seed, threshold, panel, architecture, depth, difference, statistic, budget, or decision rule was changed after the scientific SHA was frozen.

## Provenance and execution integrity

- exact neural trainings: `360/360`
- panel digest: `35898535a0df0cfe64431e5f0b6142115d40e3dbeed4a973faa9ba70b1028a30`
- panel classical revalidation: PASS
- exact fresh seed registry: PASS
- deterministic scientific receipts: PASS
- aggregate was executed twice and the JSON outputs were byte-identical: PASS
- neural evolutionary pressure: `false`
- GA↔NN feedback: never executed
- aggregate payload SHA-256: `248affbee5c902cfcb724f2f7fdf643b852bc5e0a4e603e9df97ea161f4d324d`

All frozen R4 baseline requirements passed:
- `training_count_exact`: true
- `panel_revalidated`: true
- `deterministic_receipts`: true
- `seed_registry_exact`: true
- `neural_evolutionary_pressure_absent`: true
- `r4_heterogeneity`: true
- `r4_range`: true
- `r4_signal`: true

Therefore `primary_requirements_pass = true`; the negative verdict is not caused by provenance or a failed R4 baseline gate.

## Variance trajectory

Between-candidate population variance of candidate mean neural advantages:

- `V3 = 9.413889902779758e-07`
- `V4 = 0.0012250683773673216`
- `V5 = 6.334420359523661e-05`

The descriptive trajectory is not monotonic from R3 onward: R3 is nearly saturated across candidates, R4 creates the largest between-S-box separation, and R5 greatly reduces that separation.

## Primary preregistered contrast: R4 → R5

- `Delta45 = V4 - V5 = 0.0011617241737720849`
- paired one-sided permutation p-value: `0.1121887811218878`
- `V5 / V4 = 0.05170666777911911`

The raw effect is large: R5 retains about **5.17%** of the R4 between-S-box variance, corresponding to an observed reduction of about **94.83%**.

However the frozen support rule required all three:
1. `Delta45 > 0` — PASS
2. paired permutation `p < 0.05` — **FAIL** (`0.1121887811218878`)
3. `V5/V4 <= 0.75` — PASS (`0.05170666777911911`)

Because every condition was required, the official result is `phase2ad_depth_attenuation_not_supported`.

## Secondary preregistered context: R3 → R4

- `Delta34 = V3 - V4 = -0.0012241269883770437`
- paired permutation p-value: `0.7015298470152985`
- `V4 / V3 = 1301.3413052616859`

This secondary result cannot rescue or alter the primary verdict. It shows that the measured S-box separation is extremely small at 3 rounds, becomes much larger at 4 rounds, and then becomes much smaller again at 5 rounds. Therefore the data do **not** support a simple monotonic claim that neural S-box separation decreases with every additional round.

## Per-depth signal summaries

### R3
- between-candidate variance: `9.413889902779758e-07`
- heterogeneity permutation p: `0.47595240475952405`
- candidate score range: `0.0028181692233495426`
- signal condition: true
- candidate mean advantages:
  - `0.9890767606582141`
  - `0.9865712922359089`
  - `0.9879968566679512`
  - `0.9890962610626509`
  - `0.9879085569175905`
  - `0.9893894614592584`

### R4
- between-candidate variance: `0.0012250683773673216`
- heterogeneity permutation p: `9.999000099990002e-05`
- candidate score range: `0.09919436042582302`
- signal condition: true
- candidate mean advantages:
  - `0.3753625581708507`
  - `0.27616819774502765`
  - `0.3395954249705172`
  - `0.282699810324878`
  - `0.3366224071920872`
  - `0.34212210589823383`

### R5
- between-candidate variance: `6.334420359523661e-05`
- heterogeneity permutation p: `0.1414858514148585`
- candidate score range: `0.024601346952192127`
- signal condition: true
- candidate mean advantages:
  - `0.04601124624085869`
  - `0.0396692341655977`
  - `0.042239531929941496`
  - `0.04511373694748415`
  - `0.045944384277916986`
  - `0.06427058111778983`

## Artifact receipts

All artifacts belong to workflow run `34003260315` and scientific SHA `cdad9c0fda1eaee181c5dc3cf8d05ffc869762f6`.

- R3 / `0x00000001`: artifact `9980134627`, ZIP SHA-256 `3b5b74788c1196ebee625a29e4e73fae7b01a7463f3ca351ad7bc4d066256019`
- R3 / `0x00000100`: artifact `9980136285`, ZIP SHA-256 `fcced465ebc0d0273bb9ac9c9789dc1e49f08fb1318dadfa2c77486c59a079e5`
- R4 / `0x00000001`: artifact `9980137049`, ZIP SHA-256 `aa1da702d738a2b864caa1713743a53addf013fd1496065664ca923fc1753d6a`
- R4 / `0x00000100`: artifact `9980138087`, ZIP SHA-256 `ddf76b51aed894e6d17774190e9ec11ea0b09df84745cea4cb6998befa96e429`
- R5 / `0x00000001`: artifact `9980138114`, ZIP SHA-256 `92ec279333aa0035070d58c909a1f6d30246be48feceea3fd4f14c67d6524ac5`
- R5 / `0x00000100`: artifact `9980135096`, ZIP SHA-256 `121a95fb7fdfc72ada24d753906ee8e0074daeb815fb2b2929fb66e33b41cdce`
- aggregate summary: artifact `9980143233`, ZIP SHA-256 `9da968ff8d4cf4745cd5cdf24fef7cb0b73ba874ceba3a9d490b579222d0c137`

Artifacts were configured with 90-day retention and were unexpired when this result document was frozen.

## Interpretation boundary

The experiment supplies evidence of a **large descriptive R4→R5 collapse in between-S-box neural separation**, but not enough paired-randomization evidence to satisfy the preregistered confirmatory threshold. It therefore does not establish depth attenuation as a confirmed effect.

The R3 condition also rules out a simplistic monotonic interpretation: under this exact ToySPN/training setup, candidate separation is tiny at R3, strong at R4, and weaker at R5. A future experiment may investigate a depth-dependent peak or transition, but it must be separately preregistered and must not reinterpret or retune Phase 2A-D in place.

Educational/defensive 32-bit ToySPN only. No operational key recovery, no AES/deployed-cipher weakness claim, no physical side-channel claim, no production-security claim, and no neural-resistance claim.

**Phase 2B remains blocked. No Neural Oracle is qualified by this result.**
