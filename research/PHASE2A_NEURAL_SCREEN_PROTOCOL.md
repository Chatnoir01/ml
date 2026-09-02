# Phase 2A — 100-training residual-neural screen protocol

Status: PREREGISTERED BEFORE ANY PHASE 2A NEURAL TRAINING.

## Question
At comparable classical S-box metrics, does a residual neural distinguishing signal remain in the existing toy/reduced-round research primitive?

This phase is defensive/academic and restricted to the repository's toy/reduced-round primitive. It makes no claim about deployed cryptosystems.

## Preconditions
Phase 1H warm-start mechanism confirmation passed independently (7/9 hard-admissible and structural-target runs versus 0/9 comparator; one-sided exact sign p=0.0078125). Phase 1H does NOT by itself make global Gate 1 green.

## Screen size
Exactly 100 independent neural training runs in the primary screen.

The 100 runs are organized as 10 preregistered training seeds for each of 10 classically matched S-box conditions/candidates. Candidate construction/selection must be frozen before neural outcomes are observed. If ten genuinely classically matched candidates cannot be assembled without looking at neural outcomes, Phase 2A stops and records that limitation rather than changing the design post hoc.

## Classical matching
Primary stratum target: NL >= 100, DU <= 8, max linear correlation <= 56, algebraic degree >= 6, and the existing hard SAC admissibility gate. Exact classical metrics and S-box fingerprints are recorded before training. Classical metrics remain constraints, not neural fitness in this screen.

## Neural endpoint
For every run, train the same frozen lightweight binary distinguisher on independently generated balanced data from the same toy/reduced-round primitive and fixed experimental condition. Report held-out ROC-AUC and residual advantage abs(2*AUC - 1). No training run may share examples with its held-out evaluation set.

## Independence and reproducibility
Use 100 unique training seeds. Dataset-generation seeds are deterministically derived from the training seed but separated into train/validation/test domains. Record model/config hash, S-box fingerprint, dataset provenance/hash, training seed, best validation epoch, held-out AUC and advantage.

## Primary analysis
For each of the 10 classically matched conditions, summarize 10 independent held-out AUC/advantage values with median, mean, dispersion and a confidence interval. The scientific question is whether between-S-box neural distinguishability remains materially larger than within-S-box training variation.

Do not call a tiny deviation from AUC 0.5 exploitable merely because one training run exceeds 0.5. Evidence requires repeated held-out performance and separation relative to training-seed variation.

## Anti-overfitting rule
Phase 2A is SCREENING ONLY. These 100 results may identify whether a residual signal exists and may nominate candidates/conditions for later adversarial evolution. They are not allowed to serve simultaneously as the final proof that neural-pressure evolution generalizes.

Any later neural-pressure evolution must use separate oracle seeds/data. Its final candidate must be challenged by fresh data and at least one challenger architecture/training family not used as the evolutionary oracle.

## Stop / go
STOP neural-pressure evolution if the 100-run screen shows no stable residual signal beyond training variation.

GO to a separately preregistered neural-pressure experiment only if the screen shows a repeatable residual distinguishing signal for at least one classically matched condition and the effect survives the frozen held-out analysis.

## Compute accounting
The scientific unit is one completed independent training run. Failed infrastructure jobs are not scientific observations and may be rerun only with identical frozen code/config/seed. Any scientific-code change requires a new frozen protocol/head and invalidates unfinished runs from the prior head.
