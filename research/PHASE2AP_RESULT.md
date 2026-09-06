# Phase 2A-P Result — Fresh R4 neural-separation peak confirmation

## Frozen verdict

**`phase2ap_r4_peak_supported`**

Phase 2A-P confirms, under the preregistered educational/defensive ToySPN + `byte_tanh_mlp` setup, a reproducible local maximum of measured S-box-specific neural separation at **4 rounds** relative to both **3 rounds** and **5 rounds**.

This result does **not** qualify a Neural Oracle and does **not** authorize GA↔NN feedback. Phase 2B remains blocked.

## Provenance

- public preregistration: issue #70
- draft PR: #71
- base `main`: `ee059de7c4e8681d256054a4f20e9d3bedf24668`
- protocol commit: `5706b430aee2fe5392667782a62c8485e09e4cb8`
- scientific execution SHA: `8e94777d478e7aa10e8c74e45a2d5696366c7a0b`
- workflow run: `34022405002`
- exact neural trainings: **720 / 720**
- aggregate job: `101457469052`
- aggregate computed twice and byte-identical: **true**
- aggregate payload SHA-256: `23b8e17b1c78baad84e588295566ad833093037364c29e2d698ad2c93b904d7b`
- summary artifact ID: `9985963191`
- summary artifact ZIP SHA-256: `afc44733f81b194a838ecb41468e24b6b7cf591ea540549df0a9e7ebb6f97c3a`
- frozen panel digest: `35898535a0df0cfe64431e5f0b6142115d40e3dbeed4a973faa9ba70b1028a30`
- neural evolutionary pressure: **false**

## Frozen design actually executed

- architecture: `byte_tanh_mlp`
- ToySPN depths: `(3, 4, 5)`
- input differences: `0x00000001`, `0x00000100`
- six frozen Phase-2A candidates
- 20 fresh paired dataset/model seed replicates
- per depth: `6 × 2 × 20 = 240` trainings
- total: `3 × 240 = 720` trainings
- primary tests: paired blockwise R4>R3 and R4>R5 sign-flip permutation tests
- deterministic permutations per primary side: 20,000
- Bonferroni alpha per side: `0.025`
- required neighbor/R4 block-dispersion ratio: `<= 0.75`

No outcome-based retry, seed replacement, panel change, model change, depth change, difference change, threshold change, or in-place retuning occurred after authorization.

## Prerequisite checks

All preregistered prerequisites passed:

- `training_count_exact`: **true**
- `panel_revalidated`: **true**
- `deterministic_receipts`: **true**
- `seed_registry_exact`: **true**
- `neural_evolutionary_pressure_absent`: **true**
- `r4_heterogeneity`: **true**
- `r4_range`: **true**
- `r4_signal`: **true**

Overall `requirements_pass`: **true**.

## Per-depth results

### R3

- candidate mean neural advantages:
  - `0.9885654442498313`
  - `0.9886858214994463`
  - `0.9890876753118952`
  - `0.9894459585432337`
  - `0.9891775504877633`
  - `0.9904580585763106`
- candidate mean null advantages:
  - `0.019262149542951558`
  - `0.02195410949159146`
  - `0.021565386542729856`
  - `0.019262048180521615`
  - `0.02244466286160782`
  - `0.021270569421762912`
- candidate-score range: `0.0018926143264793582`
- candidate-score population variance: `3.858773868223181e-07`
- blocked heterogeneity permutation p: `0.4783260836958152`
- mean block dispersion: `1.6921641235596552e-05`
- signal condition: **true**
- exact training count: **true**

Interpretation: R3 has very high overall neural advantage but almost no reproducible separation among the six S-box candidates under the frozen endpoint.

### R4

- candidate mean neural advantages:
  - `0.36768756881389847`
  - `0.2693688787970353`
  - `0.34400438123064014`
  - `0.2947282940347862`
  - `0.3448994679124947`
  - `0.34593486295399106`
- candidate mean null advantages:
  - `0.024586550495116107`
  - `0.025530588901801165`
  - `0.027671236028292683`
  - `0.02831306764017667`
  - `0.027972367830671602`
  - `0.022932076421656962`
- candidate-score range: `0.09831869001686316`
- candidate-score population variance: `0.001163798939987251`
- blocked heterogeneity permutation p: `4.999750012499375e-05`
- mean block dispersion: `0.001915430342872775`
- signal condition: **true**
- exact training count: **true**

Interpretation: R4 exhibits strong and highly significant S-box-specific separation under the frozen neural endpoint.

### R5

- candidate mean neural advantages:
  - `0.0648180847509141`
  - `0.035717319280360774`
  - `0.04569396810974456`
  - `0.041754834278781676`
  - `0.04997615447988792`
  - `0.054907282156829475`
- candidate mean null advantages:
  - `0.029057544252521394`
  - `0.023909887404389388`
  - `0.03344111921120825`
  - `0.02824234247455709`
  - `0.024224027327116558`
  - `0.02447289707874373`
- candidate-score range: `0.029100765470553333`
- candidate-score population variance: `8.761647335811767e-05`
- blocked heterogeneity permutation p: `0.00014999250037498125`
- mean block dispersion: `0.0007438986909960518`
- signal condition: **true**
- exact training count: **true**

Interpretation: R5 still contains statistically detectable S-box-specific heterogeneity, but the blockwise separation is substantially smaller than at R4.

## Primary preregistered peak tests

### R4 > R3

- mean R4 block dispersion: `0.001915430342872775`
- mean R3 block dispersion: `1.6921641235596552e-05`
- contrast `R4 - R3`: `0.0018985087016371784`
- R3/R4 ratio: `0.00883438089960367`
- one-sided paired permutation p: `4.999750012499375e-05`
- preregistered side verdict: **PASS**

This satisfies all frozen requirements: positive contrast, `p < 0.025`, and ratio `<= 0.75`.

### R4 > R5

- mean R4 block dispersion: `0.001915430342872775`
- mean R5 block dispersion: `0.0007438986909960518`
- contrast `R4 - R5`: `0.0011715316518767231`
- R5/R4 ratio: `0.3883715707877676`
- one-sided paired permutation p: `4.999750012499375e-05`
- preregistered side verdict: **PASS**

This also satisfies all frozen requirements: positive contrast, `p < 0.025`, and ratio `<= 0.75`.

Because **both** preregistered sides pass and all prerequisites pass, the frozen aggregate verdict is:

**`phase2ap_r4_peak_supported`**

## Evidence artifacts

Summary:
- artifact ID `9985963191`
- artifact name `phase2ap-summary-8e94777d478e7aa10e8c74e45a2d5696366c7a0b`
- ZIP SHA-256 `afc44733f81b194a838ecb41468e24b6b7cf591ea540549df0a9e7ebb6f97c3a`

Cell artifacts:
- R5-d1: ID `9985955208`, SHA-256 `ceedced8546c890f5d7bf42064b68a20d61404a345d072695ddb18ef8853bd08`
- R5-d100: ID `9985953214`, SHA-256 `9bc3ae3ed31c0b1914a38906e4e49a7ad33f6b668111ba0be35bf741c3d8d34a`
- R3-d100: ID `9985952941`, SHA-256 `b3fd4fbdcc8ab1941880fe02dff08502026f5bb3beb0d188ceb97ee0d9a33e2c`
- R4-d1: ID `9985952789`, SHA-256 `144b5405122c76bc9caa0011b7e81ab7a7fe6dc6d46ad8f0a90a5240d7fb7a22`
- R3-d1: ID `9985952495`, SHA-256 `5a73f86383167043756fba0d5eae4db7e886781d760047be3ccf91a323a76087`
- R4-d100: ID `9985949978`, SHA-256 `0e6b0ed987ec940e6e9acde7e94118f3f94f2eaccb164fa9e0d7e3ee112928ec`

## Scientific interpretation

The frozen Phase 2A-P evidence supports a **local R4 peak**, not a monotonic rule that more rounds always reduce signal. Under this exact toy pipeline:

- R3 is extremely easy for the network globally, but the six S-box candidates look almost indistinguishable from one another;
- R4 produces the largest reproducible candidate-specific separation;
- R5 retains detectable candidate heterogeneity, but markedly less blockwise separation than R4.

This is mechanistic evidence about the frozen ToySPN/neural measurement regime. It does not by itself establish that the candidate ordering is architecture-independent, transferable to new panels, or suitable as an evolutionary fitness signal.

## Interpretation boundary / safety gate

This experiment is educational/defensive and uses the repository's toy 32-bit SPN only.

It does **not** establish:
- AES weakness or superiority over AES;
- weakness of any deployed cipher;
- operational key recovery;
- a security proof;
- physical DPA/side-channel resistance;
- production readiness;
- neural resistance;
- a qualified Neural Oracle;
- successful GA↔NN co-evolution.

**Phase 2B remains blocked.** A later Neural Oracle qualification must be separately preregistered and must use fresh confirmation evidence rather than silently treating this R4-mechanism result as an oracle qualification.
