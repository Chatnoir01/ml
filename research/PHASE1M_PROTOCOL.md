# Phase 1M — DU-hotspot bridge development protocol

## Status

Preregistered development experiment. The design decisions in issues #27–#40 were recorded before Phase-1M implementation. This repository protocol freezes the exact budget and execution rules before any Phase-1M scientific development seed is run.

Phase 1M follows the frozen Phase-1L negative result. Phase 1L showed that ITO-aware selection lowered terminal ITO, but the dominant classical bottleneck remained differential uniformity around 10 and no terminal candidate reached the structural/hard-admissible target.

Phase 1M therefore tests a **proposal mechanism** for crossing the DU frontier. It does not weaken hard constraints, add scalar fitness weights, claim novelty, or enable the neural oracle.

## Fresh seed split

Development seeds:

- 2111
- 2113
- 2129
- 2131
- 2137

Reserved confirmation seeds, quarantined during development:

- 2203
- 2207
- 2213
- 2221
- 2237
- 2239
- 2243
- 2251
- 2267

The Phase-1L reserved seeds 2003–2069 remain separately quarantined and are not recycled.

## Frozen hard constraints

Unchanged:

- nonlinearity >= 100
- differential uniformity <= 8
- max absolute linear correlation <= 64
- algebraic degree >= 6
- |SAC - 0.5| <= 0.05

The structural target excludes SAC and requires the first four conditions.

## Experimental question

Can a DDT-max-cell hotspot-directed swap proposal operator produce DU <= 8 candidates more reliably than ordinary random swap proposals under an identical, fully charged classical evaluation budget, while protecting the other classical gates and preserving the staged ITO signal?

## Frozen operator contract

For a bijective 8x8 S-box, the hotspot operator must:

1. build the DDT;
2. inspect nonzero input differences only;
3. find every DDT cell attaining the current maximum differential uniformity;
4. identify S-box input positions participating in those maximum-count transitions;
5. generate bijective swap proposals using hotspot positions as anchors;
6. return deterministic output for the same S-box and RNG seed;
7. avoid duplicate proposals within one call;
8. expose proposal metadata sufficient to audit the motivating hotspot;
9. never compute ITO or any neural score internally;
10. never score a proposal outside the counted evaluation ledger.

If hotspot-directed unique proposals cannot fill the requested count, deterministic random-swap fallback is allowed, but those proposals remain fully charged when evaluated.

## Frozen exact budget

Each arm receives exactly **340 unique full classical CryptoShield evaluations per development seed**.

For Arms A and B this is a hard ledger cap, not a generation-derived estimate. The ledger counts:

- initial fresh-population evaluations;
- every unique proposal receiving a full classical evaluation;
- proposals later rejected by selection.

A cached re-read of an already evaluated S-box does not consume a second evaluation. Search must terminate at exactly 340 unique classical evaluations.

ITO evaluations are counted and reported separately. A and B use the same ITO shortlist/selection policy so the proposal mechanism is the intended experimental difference.

Arm C uses the historical Phase-1L `feasibility_first` configuration that consumes exactly 340 full classical evaluations.

## Three frozen arms

### Arm A — DU-hotspot proposals + staged ITO Pareto

- fresh initial population shared with B and C;
- mutation proposals anchored on current maximum-DU DDT hotspots;
- every inspected unique proposal is charged to the 340 classical budget;
- population/terminal selection protects classical feasibility and uses staged ITO-aware Pareto/NSGA-II on the shortlist;
- no scalar weighted objective.

### Arm B — ordinary swap proposals + staged ITO Pareto

Identical to Arm A except proposal generation uses ordinary random swap mutation with the same proposal count/ledger discipline. It uses the same fresh initial population, classical constraints, shortlist policy, ITO policy, and exact 340 classical budget.

This is the primary mechanism ablation.

### Arm C — historical feasibility-first GA

Frozen Phase-1L historical comparator:

- population size: 20
- generations: 10
- elite count: 4
- tournament size: 3
- mutation swaps: 3
- crossover rate: 0.0
- immigrant fraction: 0.10
- offspring multiplier: 2
- ranking mode: `feasibility_first`

Exact classical budget: 340.

Arm C is descriptive; the preregistered gate is primarily A versus B.

## Terminal reporting

For A and B report at minimum:

- exact classical evaluation count;
- ITO evaluation count;
- best terminal DU;
- terminal count with DU <= 8;
- terminal count satisfying NL >= 100, max |LAT| <= 64 and algebraic degree >= 6;
- hard-admissible count;
- structural-target count;
- minimum terminal ITO;
- terminal metrics and fingerprints;
- initial-population SHA-256 digest;
- deterministic scientific payload digest.

Arm C reports its best classical metrics, ITO, admissibility/structural status, exact classical count and initial-population digest.

## Frozen development prerequisite for confirmation

All conditions are required across the five fresh development seeds:

1. aggregate terminal DU<=8 count in Arm A > Arm B;
2. Arm A reaches at least one terminal DU<=8 candidate on at least 3/5 seeds;
3. median terminal best DU(A) < median terminal best DU(B); if equal, Arm A must have strictly more per-seed best-DU wins than losses;
4. aggregate terminal count satisfying NL>=100, max |LAT|<=64 and degree>=6 in A >= B;
5. median minimum terminal ITO(A) <= median minimum terminal ITO(B) + 0.02;
6. A and B each consume exactly 340 unique full classical evaluations on every seed, including rejected proposals;
7. A/B/C start from the same initial-population digest within each seed;
8. a fixed-seed rerun produces the same scientific payload digest excluding timestamps/runtime;
9. every development seed is exactly the registered Phase-1M set and confirmation seeds remain unused;
10. no neural model, neural fitness, or neural oracle is executed.

If any condition fails, verdict is `phase1m_dev_fail`, confirmation remains blocked, parameters are not tuned in place, and the negative result is preserved.

If all conditions pass, a separate confirmation protocol must be committed before any reserved confirmation seed is run. No development parameter may be changed between development and confirmation.

## No-run lock

The Phase-1M scientific development matrix must not be executed until all of the following exist on the branch:

- this frozen protocol;
- registered Phase-1M seeds;
- red-first contract evidence;
- implementation with exact ledger accounting;
- green Python 3.10/3.11/3.12 CI;
- green historical benchmark;
- inspected PR diff;
- a frozen scientific commit SHA;
- workflow preflight that rejects unregistered seeds and verifies the frozen constants.

Ordinary unit/CI tests are allowed before that point. Scientific development seeds are not.

## Interpretation boundary

A positive Phase-1M result would support only the claim that the DDT-hotspot proposal mechanism improves the frozen DU<=8 bridge under this matched-budget design while meeting the non-regression guards. It would not prove deployment-grade cryptography, superiority to AES, practical side-channel resistance, or neural co-evolution success.
