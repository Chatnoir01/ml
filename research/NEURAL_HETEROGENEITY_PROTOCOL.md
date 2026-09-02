# Neural heterogeneity challenger — preregistered protocol

## Status and scope

This is an **exploratory reduced-round diagnostic** on the educational 32-bit `ToySPN` only.
It does not change Global Gate 1, does not authorize neural pressure inside the GA, and does
not claim relevance to deployed ciphers.

The protocol is frozen before any result from this experiment is produced.

## Motivation

The completed `NEURAL100` screen observed a residual neural signal but did not establish
reproducible heterogeneity across ten classically matched S-boxes (`p = 0.3525`). The next
question is therefore narrower:

> Does a reproducible S-box-specific neural signal emerge when the same matched S-box panel
> is challenged across multiple round counts, multiple input differences, and an independent
> challenger architecture?

The S-box panel is unchanged from `neural100_candidates.py`; every candidate must revalidate
exactly to:

- nonlinearity = 100
- differential uniformity = 8
- max linear correlation = 56
- algebraic degree = 7
- SAC = 0.5

No candidate is added, removed, or reordered based on neural results.

## Factorial design

The experiment contains exactly:

- 10 matched S-boxes
- 3 round counts: `3`, `4`, `5`
- 4 input differences:
  - `0x00000001`
  - `0x00000100`
  - `0x00010001`
  - `0x01010101`
- 2 neural architectures:
  - `bit_relu_mlp`
  - `byte_tanh_mlp`
- 5 paired replicates per S-box / regime / architecture

Total neural trainings:

`10 × 3 × 4 × 2 × 5 = 1200`.

A **regime** is one `(round_count, input_difference)` pair. There are 12 regimes.
A **block** for the primary permutation test is one `(regime, architecture, replicate)` tuple.
There are therefore `12 × 2 × 5 = 120` blocks, each containing the ten matched S-boxes.

## Fixed ToySPN keys

The fixed key pool is:

```text
0x243F6A88
0x85A308D3
0x13198A2E
0x03707344
0xA4093822
0x299F31D0
```

For `r` rounds, the cipher uses the first `r + 1` keys. Therefore the only experimental
change in cipher depth is the number of repeated ToySPN rounds; no key is tuned per S-box.

## Dataset and model budget

Every training uses:

- balanced pair count: `8192`
- the repository's existing deterministic train/validation/test split
- the same pair generator and block-disjoint provenance rules used by `NEURAL100`

Fresh base replicate seeds are:

- dataset bases: `(510001, 510013, 510031, 510047, 510059)`
- model bases: `(610001, 610019, 610031, 610043, 610051)`

Regimes are indexed deterministically in lexicographic product order:

`rounds=(3,4,5)` outer, then the four input differences in the declaration order above.

For regime index `g ∈ [0,11]` and replicate `r ∈ [0,4]`:

- dataset seed = `DATASET_BASE[r] + 1000*g`
- `bit_relu_mlp` model seed = `MODEL_BASE[r] + 1000*g`
- `byte_tanh_mlp` model seed = `MODEL_BASE[r] + 1000*g + 100000`

These seed ranges are disjoint from the completed `NEURAL100` seed ranges.

## Frozen architectures

### A — bit_relu_mlp

Representation: the same 96 binary features as `NEURAL100`: 32 bits of left ciphertext,
32 bits of right ciphertext, and 32 bits of their XOR.

Network:

- input 96
- hidden 64, ReLU
- scalar sigmoid output
- epochs 24
- batch size 256
- Adam learning rate 0.002
- L2 weight decay 1e-4

This architecture intentionally preserves the prior screen's model family.

### B — byte_tanh_mlp

Independent challenger representation: 12 normalized byte-valued features consisting of
four bytes of left ciphertext, four bytes of right ciphertext, and four bytes of their XOR.
Each byte is mapped from `[0,255]` to `[-1,1]`.

Network:

- input 12
- hidden 48, tanh
- hidden 24, tanh
- scalar sigmoid output
- epochs 32
- batch size 256
- Adam learning rate 0.003
- L2 weight decay 1e-4

The challenger differs in representation, depth, activation, and optimization budget.

## Endpoint

For every training, record at minimum:

- validation AUC
- test AUC
- neural advantage `2*abs(AUC-0.5)`
- matched shuffled-label null AUC and null advantage
- candidate fingerprint
- regime, architecture, replicate
- exact dataset/model seeds
- exact classical metrics

No model is selected by validation AUC across runs; all frozen trainings are retained.

## Primary S-box heterogeneity test

For each S-box, compute its mean neural advantage across all 120 blocks.
The observed primary statistic is the population variance of those ten S-box means.

Null distribution:

- use exactly `10000` permutations;
- in each permutation, independently shuffle the ten S-box labels **within every block**;
- do not shuffle round count, input difference, architecture, or replicate labels;
- permutation RNG seed = `920001`.

One-sided p-value uses the standard `(1 + exceedances)/(1 + repetitions)` correction.

This blocked test asks whether stable S-box identity explains more variation than expected
once all declared nuisance factors are held fixed.

## Challenger-replication checks

The same blocked heterogeneity test is repeated separately for each architecture, using:

- `5000` permutations per architecture
- permutation seed `920101` for `bit_relu_mlp`
- permutation seed `920201` for `byte_tanh_mlp`

Additionally compute Spearman rank correlation between the ten per-S-box mean advantages
from the two architectures. Ties use average ranks.

## Frozen verdict

The aggregate diagnostic is exactly one of:

- `replicated_sbox_heterogeneity`
- `global_heterogeneity_not_replicated`
- `residual_signal_no_sbox_heterogeneity`
- `no_exploitable_residual_at_frozen_budget`

`replicated_sbox_heterogeneity` requires **all** of:

1. exactly 1200 trainings are present with complete provenance;
2. global blocked heterogeneity `p < 0.01`;
3. global range of the ten S-box mean advantages is at least `0.015`;
4. `bit_relu_mlp` heterogeneity `p < 0.05`;
5. `byte_tanh_mlp` heterogeneity `p < 0.05`;
6. Spearman correlation between architecture-specific S-box means is at least `0.40`;
7. at least one S-box has overall mean neural advantage at least `0.04` and exceeds its
   overall mean null advantage by at least `0.02`.

If conditions 2–3 and 7 hold but any challenger-replication condition 4–6 fails, verdict is
`global_heterogeneity_not_replicated`.

If condition 7 holds but global heterogeneity conditions fail, verdict is
`residual_signal_no_sbox_heterogeneity`.

Otherwise verdict is `no_exploitable_residual_at_frozen_budget`.

## Interpretation gate

Even `replicated_sbox_heterogeneity` does **not** make Global Gate 1 green and does not by
itself enable Phase 2. It would only justify a later, separately preregistered experiment that
tests whether a neural score can provide useful evolutionary pressure after the required
fresh-population classical transfer is demonstrated.

Any negative or mixed result is retained as evidence if code and CI are green.
