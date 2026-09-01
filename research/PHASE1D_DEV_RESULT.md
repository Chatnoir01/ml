# Phase 1D — verified frontier continuation development result

Status: **development negative; confirmation not executed; global Gate 1 remains RED**.

## Frozen provenance

The historical Phase-1B frontier candidate was reproduced before accepting any continuation result:

- seed `307`
- `NL=98`
- `DU=8`
- maximum linear correlation `60`
- algebraic degree `7`
- SAC `0.501708984375`
- fingerprint `d0260bcfbff19b1d43c1e2f41d923c6096d48ef0e3e4e1e78c088f81e02a1bcc`

Historical receipt workflow run: `33350548034`.

Receipt artifact: `9743448001`, digest `sha256:dfcfca33d05dcf9efdb8aa08fc9f5ab74d9969ed53b6b62e1a0d7de550daa3c1`.

The receipt gate therefore passed exactly.

## Frozen development run

Workflow run: `33350556385`.

Frozen experiment SHA: `9f6eb7b2e9855ef3e3cabbd2f8a0306241f94ece`.

Development seeds: `701, 709, 719, 727, 733`.

Reserved confirmation seeds remain unused: `809, 811, 821, 823, 827, 829, 839, 853, 857`.

Each configuration used exactly 600 adaptive evaluations and 600 equal-budget direct-comparator evaluations per seed, both starting from the same verified historical candidate.

## Configuration results

| Configuration | Adaptive admissible | Adaptive `NL>=100, DU<=8` | Direct `NL>=100, DU<=8` | Adaptive wins | Direct wins | Ties | Median adaptive NL / DU / corr |
|---|---:|---:|---:|---:|---:|---:|---|
| `beam1_swap1` | 0/5 | 0/5 | 0/5 | 1 | 0 | 4 | 98 / 8 / 60 |
| `beam4_swap1` | 0/5 | 0/5 | 0/5 | 1 | 0 | 4 | 98 / 8 / 60 |
| `beam8_swap1` | 0/5 | 0/5 | 0/5 | 1 | 0 | 4 | 98 / 8 / 60 |
| `beam16_swap1` | 0/5 | 0/5 | 0/5 | 1 | 0 | 4 | 98 / 8 / 60 |
| `beam8_swap2` | 0/5 | 0/5 | 0/5 | 5 | 0 | 0 | 98 / 8 / 60 |
| `beam8_swap3` | 0/5 | 0/5 | 0/5 | 1 | 2 | 2 | 98 / 8 / 60 |

Across all 30 adaptive development runs, zero finished with `NL>=100` while preserving `DU<=8`, and zero became hard-admissible.

`beam8_swap2` is diagnostically the strongest adaptive-vs-direct configuration (5/5 adaptive wins), but it still failed the preregistered success prerequisite. It therefore cannot advance to confirmation.

## Artifact receipts

- `beam1_swap1`: artifact `9743544027`, `sha256:44129f1124bb373d00cc21ad5d523f292865e1f4c609052cef1279403b2c76d0`
- `beam4_swap1`: artifact `9743580400`, `sha256:acf19871272da325eef1f909de875e8755f4b17ff296d1f99acdeca791e92edc`
- `beam8_swap1`: artifact `9743599351`, `sha256:f41f23a7e7ee93aacf1235dbdcebc97348977f003a619fb21394d7a01550985a`
- `beam16_swap1`: artifact `9743573927`, `sha256:93262777555bf9bef0d70206126375753661c6147a3103cb171dd51c1b12af8f`
- `beam8_swap2`: artifact `9743624867`, `sha256:a6e8ad5bf7befc5610dfa7c4a4947d437f866a5b8af6928f8b59f4a5dd476027`
- `beam8_swap3`: artifact `9743613789`, `sha256:287cd9fedf64894ce3c9321e9a8def1b69af133032a712dd4feea818ce3b76cb`

## Preregistered stop-rule verdict

The frozen protocol states that if no configuration achieves `NL>=100` with `DU<=8` on any development seed, Phase 1D confirmation is not executed.

That condition is met exactly. Therefore:

1. no Phase-1D configuration is promoted to confirmation;
2. confirmation seeds `809..857` remain unused;
3. no Gate-1 claim is made;
4. the neural-oracle phase remains blocked;
5. the negative continuation result is retained as evidence rather than retuned after observation.

## Scientific interpretation

The experiment shows that preserving the known `DU=8` frontier is reproducible under warm start, but the tested local swap/beam operators do not cross the observed `NL=98` plateau within the frozen 600-evaluation budget. Adaptive two-swap continuation outperforms direct sampling by the experiment's rank on all five development seeds, yet this advantage is secondary because it never produces the required structural improvement to `NL>=100`.

The next classical experiment, if pursued, should change the neighborhood/operator family rather than merely increase beam width or reuse these confirmation seeds. Any new development/confirmation seed sets must be registered before execution.
