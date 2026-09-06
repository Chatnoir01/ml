# Phase 2A-S — Neural Signal Attenuation Across Round Depth

## Status

**PREREGISTERED — NO SCIENTIFIC TRAINING AUTHORIZED YET**

Phase 2A-R ended `phase2ar_inconclusive_signal`: the frozen six-S-box panel carried strong S-box-specific neural heterogeneity at 4 rounds but failed the preregistered heterogeneity requirement at 5 rounds. Phase 2A-S tests that uncertainty directly. It is a diagnostic/replication experiment only and cannot authorize GA↔NN feedback.

## Scientific question

Holding architecture, representation, input-difference family, frozen S-box panel, dataset/model seed pairing, training hyperparameters, and statistical procedure fixed, does S-box-specific neural separation weaken as ToySPN depth increases from 3 to 4 to 5 rounds?

## Frozen panel

Reuse exactly the six committed candidates in `src/adversarial_sbox/phase2a_candidates.py`.

Panel digest:
`35898535a0df0cfe64431e5f0b6142115d40e3dbeed4a973faa9ba70b1028a30`

Every candidate must revalidate before training:
- bijective 8x8 S-box;
- DU = 8;
- NL = 100;
- max |LAT| = 56;
- algebraic degree = 7;
- SAC within the existing hard bound.

No new candidate selection is allowed.

## Frozen neural regime

Use the existing deterministic `byte_tanh_mlp` ToySPN training implementation from Phase 2A/2A-R.

Only round depth changes:
- R3: 3 rounds;
- R4: 4 rounds;
- R5: 5 rounds.

Input-difference family is fixed for every depth:
- `0x00000001`
- `0x00000100`

No architecture, representation, optimizer, sample-count, epoch-count, null-label procedure, or score definition may change between depths.

## Fresh paired neural seeds

The scientific implementation must freeze five fresh dataset seeds and five fresh model seeds before the execution marker is created. They must be checked against the repository for prior scientific use and then committed in code/protocol before any training. The same five paired seeds are reused across all six candidates, both differences, and all three depths.

No seed may be retried/replaced because of its result.

## Training budget

Per depth:
- 6 candidates x 2 differences x 5 paired replicates = 60 trainings.

Total:
- 3 depths x 60 = **180 neural trainings exactly**.

No neural score may enter evolution.

## Frozen endpoints

Per training, preserve the Phase 2A endpoint and deterministic null-label diagnostic.

Per depth and candidate:
- candidate score = mean neural advantage across its 10 trainings.

For each depth independently:
- blocked S-box heterogeneity permutation test with exactly 10,000 deterministic permutations;
- candidate score range;
- Phase-2A signal condition;
- mean candidate neural advantage;
- dispersion across candidate means.

Across depths compute:
- Spearman rho(R3,R4);
- Spearman rho(R4,R5);
- ratio of candidate-score range R4/R3 and R5/R4;
- ratio of mean neural advantage R4/R3 and R5/R4.

The pre-existing rank-stability threshold remains rho >= 0.60.

## Primary preregistered attenuation test

Define each depth as carrying **reliable S-box-specific separation** only if all Phase-2A signal prerequisites pass:
1. exact provenance/training count;
2. frozen panel revalidation;
3. heterogeneity permutation p < 0.05;
4. candidate score range >= 0.015;
5. at least one candidate mean neural advantage >= 0.04 and exceeds its depth mean null advantage by >= 0.02;
6. deterministic receipts.

Classification:
- R3 and R4 reliable, R5 not reliable: `phase2as_depth_attenuation_supported`;
- R3 reliable, R4 and R5 not reliable: `phase2as_early_attenuation_supported`;
- R3/R4/R5 all reliable: `phase2as_no_reliability_loss`;
- any non-monotone reliability pattern (for example R3 fail, R4 pass): `phase2as_nonmonotone_signal`;
- otherwise: `phase2as_inconclusive`.

The classification is frozen before scientific execution and is not an oracle qualification verdict.

## Secondary descriptive evidence

The exact p-values, ranges, mean advantages, dispersion, adjacent rank correlations, and attenuation ratios must be reported regardless of primary classification. They are descriptive and may motivate a separately preregistered follow-up, but they cannot override the primary classification.

## Reproducibility / execution lock

Before scientific execution:
1. protocol committed;
2. fresh seed registry committed;
3. RED contract tests recorded before implementation where applicable;
4. implementation and aggregate tests GREEN;
5. exact 180-training workflow committed but dormant;
6. Python 3.10/3.11/3.12 CI GREEN;
7. historical Phase-1 benchmark GREEN;
8. PR diff inspected;
9. only then create `research/PHASE2AS_EXECUTE.md` containing `AUTHORIZED_PHASE2AS_DEPTH_ATTENUATION`.

The marker commit SHA is the frozen scientific SHA. No scientific parameter may change after observing results.

## Interpretation boundary

This experiment is educational/defensive and uses ToySPN only. It performs no operational key recovery and makes no claim of AES/deployed-cipher weakness, physical side-channel resistance, production security, neural resistance, or successful GA↔NN co-evolution.

Regardless of outcome, **Phase 2B GA↔NN remains blocked**. Any Neural Oracle qualification requires a separately preregistered fresh confirmation experiment.