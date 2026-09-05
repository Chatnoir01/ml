# Phase 1N — joint DU / nonlinearity bridge protocol

## Status

Preregistered development experiment. Issues #43–#47 freeze the hypothesis, operator, matched budget, fresh seed split, and development gate before any Phase-1N implementation or scientific execution.

Phase 1N follows the frozen negative Phase-1M result. Phase 1M produced one terminal DU=8 candidate on seed 2131 under DDT-hotspot proposals, but that candidate had NL=98 and Phase 1M failed its preregistered DU reproducibility requirement. Phase 1M is not retuned.

Phase 1N tests a new proposal mechanism intended to preserve/improve the current worst Walsh coefficient while retaining DDT-hotspot pressure. It does not weaken hard constraints, add scalar fitness weights, claim novelty, or enable the neural oracle.

## Fresh seed split

Development seeds:

- 2309
- 2311
- 2333
- 2339
- 2341

Reserved confirmation seeds, quarantined during development:

- 2401
- 2411
- 2417
- 2423
- 2437
- 2441
- 2447
- 2459
- 2467

All earlier development and reserved/confirmation seeds remain quarantined and are not recycled.

## Frozen hard constraints

Unchanged:

- nonlinearity >= 100
- differential uniformity <= 8
- max absolute linear correlation <= 64
- algebraic degree >= 6
- |SAC - 0.5| <= 0.05

The structural target excludes SAC and requires the first four conditions.

The primary Phase-1N JOINT target is:

- DU <= 8
- NL >= 100
- max |LAT| <= 64
- algebraic degree >= 6

No hard ITO threshold is introduced.

## Experimental question

Can a joint DDT + Walsh-guided one-swap proposal mechanism produce JOINT-target terminal candidates more reliably than the frozen Phase-1M DDT-hotspot-only proposal mechanism under an identical, fully charged classical evaluation budget, while not regressing the DU bridge or staged ITO signal?

## Frozen joint proposal contract

For a bijective 8x8 S-box, the Phase-1N joint proposal operator must:

1. build the DDT and identify every maximum non-trivial DDT cell;
2. identify the S-box input positions participating in those maximum-count transitions;
3. compute current worst absolute Walsh/LAT coefficients relevant to vectorial nonlinearity;
4. generate bijective one-swap proposals with at least one endpoint anchored in a maximum-DU hotspot;
5. prefer endpoint pairs whose exact local contribution delta moves at least one current worst Walsh coefficient toward zero;
6. expose audit metadata sufficient to reconstruct the motivating DDT hotspot and Walsh pair: input/output difference, hotspot count/positions, input/output Walsh masks, old Walsh coefficient, predicted delta, endpoints, and fallback flag;
7. return deterministic output for the same S-box and RNG seed;
8. avoid duplicate proposals within one call;
9. never call full `evaluate_classical`, ITO, a neural metric, or any candidate-wide post-swap metric inside proposal generation;
10. never score a proposed candidate outside the counted classical ledger.

The operator may use the parent S-box's DDT and Walsh structure because these determine proposal geometry. Candidate metrics after mutation are only learned through the charged full classical evaluator.

If no unique Walsh-improving hotspot-anchored swap can fill the requested proposal count, deterministic Phase-1M hotspot-only fallback is allowed. Fallback proposals remain fully charged when evaluated and are reported separately.

## Frozen exact budget

Each arm receives exactly **340 unique full classical CryptoShield evaluations per development seed**.

For Arms A and B the ledger counts:

- the shared fresh initial population;
- every unique proposal receiving a full classical evaluation;
- every proposal later rejected by selection.

A cached re-read of an already evaluated S-box does not consume a second evaluation. Search must terminate at exactly 340 unique classical evaluations.

ITO evaluations are counted separately. A and B use the same shortlist and staged ITO-aware selection policy so proposal generation is the intended experimental difference.

Arm C is the historical `feasibility_first` reference at its frozen 340-evaluation configuration.

## Three frozen arms

### Arm A — joint DDT + Walsh proposals

- fresh initial population shared with B and C;
- joint DDT-hotspot / worst-Walsh-guided one-swap proposal generation;
- every inspected unique proposal charged to the 340 classical budget;
- frozen staged ITO-aware Pareto/NSGA-II shortlist and parent selection;
- no scalar weighted objective.

### Arm B — Phase-1M hotspot-only ablation

Identical to Arm A except proposal generation uses the frozen Phase-1M DDT-hotspot-only operator. Same initial population, exact classical budget, shortlist size, parent count, ITO policy, and terminal selection.

This is the primary mechanism ablation.

### Arm C — historical feasibility-first GA

Frozen historical comparator:

- population size: 20
- generations: 10
- elite count: 4
- tournament size: 3
- mutation swaps: 3
- crossover rate: 0.0
- immigrant fraction: 0.10
- offspring multiplier: 2
- ranking mode: `feasibility_first`
- exact classical evaluations: 340

Arm C is descriptive; the preregistered Phase-1N gate is primarily A versus B.

## Frozen engine geometry

For Arms A and B:

- population size: 20
- shortlist size: 8
- parent count: 4
- proposals per parent: 4
- proposals per generation: 16
- generations: 20
- exact classical total: 20 + 20 x 16 = 340
- ITO non-inferiority tolerance: +0.02

## Terminal reporting

For A and B report at minimum:

- exact classical evaluation count;
- ITO evaluation count;
- best terminal DU;
- terminal DU<=8 count;
- terminal protected-classical count (NL>=100, max |LAT|<=64, degree>=6);
- terminal JOINT-target count;
- hard-admissible count;
- structural-target count;
- minimum terminal ITO;
- terminal metrics and fingerprints;
- initial-population SHA-256 digest;
- proposal audit SHA-256;
- joint-guided/fallback proposal counts;
- deterministic scientific payload digest.

Arm C reports its best classical metrics, ITO, admissibility/structural status, exact classical count and initial-population digest.

## Frozen development prerequisite for confirmation

All conditions are required across the five fresh development seeds:

1. aggregate terminal JOINT-target count in Arm A > Arm B;
2. Arm A reaches at least one terminal JOINT-target candidate on at least 2/5 seeds;
3. Arm A does not regress the DU bridge: seeds with terminal DU<=8 in A >= B and paired best-DU wins >= losses;
4. median terminal best DU(A) <= median terminal best DU(B);
5. aggregate protected-classical terminal count in A >= B;
6. median minimum terminal ITO(A) <= median minimum terminal ITO(B) + 0.02;
7. A/B/C each consume exactly 340 unique full classical evaluations on every seed, including rejected proposals;
8. A/B/C start from the same initial-population digest within each seed;
9. a fixed-seed rerun produces the same canonical scientific payload digest excluding timestamps/runtime;
10. every development seed is exactly the registered Phase-1N set and confirmation seeds remain unused;
11. no neural model, neural fitness, or neural oracle is executed.

If any condition fails, verdict is `phase1n_dev_fail`, confirmation remains blocked, parameters are not tuned in place, and the negative result is preserved.

If all conditions pass, a separate confirmation protocol must be committed before any reserved confirmation seed is run. No development parameter may be changed between development and confirmation.

## No-run lock

The Phase-1N scientific development matrix must not execute until all of the following exist on the branch:

- issues #43–#47;
- this frozen protocol;
- registered Phase-1N seeds;
- red-first contract evidence;
- implementation with exact ledger accounting;
- green Python 3.10/3.11/3.12 CI;
- green historical benchmark;
- inspected PR diff;
- a frozen scientific commit SHA;
- workflow preflight verifying registered seeds and frozen constants;
- an explicit `PHASE1N_EXECUTE.md` authorization marker committed only after the engineering checks above.

Ordinary unit/CI tests are allowed before that point. Scientific development seeds are not.

## Interpretation boundary

A positive Phase-1N development result would support only the claim that the joint DDT+Walsh proposal mechanism improved the frozen JOINT DU/NL bridge under this matched-budget design while satisfying the preregistered non-regression guards.

It would not prove superiority to AES, deployment-grade cryptography, practical side-channel resistance, or neural co-evolution success. Global Gate 1 and the neural oracle remain blocked until their own preregistered evidence requirements are met.
