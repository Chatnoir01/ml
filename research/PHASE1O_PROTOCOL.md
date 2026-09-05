# Phase 1O — multi-hotspot Walsh plateau repair protocol

## Status

Preregistered development experiment. Issues #49–#53 freeze the hypothesis, operator, matched budget, fresh seed split and development gate before any Phase-1O implementation or scientific execution.

Phase 1O follows the frozen Phase-1N negative result. Phase 1N made the DU<=8 bridge substantially more reproducible (3/5 fresh development seeds versus 1/5 for hotspot-only; median best DU 8 versus 10) but produced no terminal candidate satisfying the JOINT target because all DU<=8 terminals remained at NL 98 or 96.

Phase 1O therefore tests whether proposal geometry that treats the entire tied maximum-Walsh plateau of the parent can preserve/repair vectorial nonlinearity better than sampling one worst Walsh coefficient at a time. Phase 1N remains frozen and is not retuned.

## Fresh seed split

Development seeds:

- 2503
- 2521
- 2531
- 2539
- 2543

Reserved confirmation seeds:

- 2609
- 2617
- 2621
- 2633
- 2647
- 2657
- 2663
- 2671
- 2683

All earlier development and reserved/confirmation seeds remain quarantined.

## Frozen hard constraints

Unchanged:

- nonlinearity >= 100
- differential uniformity <= 8
- max absolute linear correlation <= 64
- algebraic degree >= 6
- |SAC - 0.5| <= 0.05

The primary JOINT target is:

- DU <= 8
- NL >= 100
- max |LAT| <= 64
- algebraic degree >= 6

No hard ITO threshold is introduced.

## Experimental question

Can a maximum-DDT-hotspot-anchored proposal operator that optimizes the parent’s entire tied maximum-Walsh plateau produce more JOINT-target terminal candidates than the frozen Phase-1N single-worst-Walsh proposal operator under the same exact classical budget and the same staged ITO-aware selection policy?

## Frozen multi-hotspot proposal contract

For a bijective 8x8 parent S-box, the operator must:

1. build the DDT and identify every maximum non-trivial DDT cell;
2. identify the S-box input positions participating in those maximum-count transitions;
3. compute the full set M of nonzero-output-mask Walsh/LAT coefficients whose absolute value equals the parent vectorial maximum;
4. generate one-swap bijective proposals with at least one endpoint anchored in a maximum-DU hotspot;
5. for each swap considered by proposal generation, compute only the exact two-position local Walsh delta for every coefficient in M;
6. compute a parent-local plateau score from those deltas only;
7. prefer proposals lexicographically by:
   - lower predicted maximum absolute coefficient over M;
   - then more members of M strictly improved;
   - then fewer members of M worsened;
   - then larger total absolute-coefficient reduction;
   - then deterministic endpoint/mask tie-breaks;
8. expose audit metadata sufficient to reconstruct the motivating DDT hotspot, size/value of M, predicted plateau score, endpoints and fallback status;
9. return deterministic output for the same S-box and RNG seed;
10. avoid duplicate proposals within one call;
11. never call full `evaluate_classical`, ITO, neural scores, or candidate-wide post-swap DDT/LAT/classical metrics inside proposal generation;
12. never score an inspected candidate outside the counted classical ledger.

If the multi-hotspot mechanism cannot fill the requested unique proposal count, deterministic fallback to the frozen Phase-1N single-worst-Walsh operator is allowed. Fallback candidates are fully charged and reported separately.

## Frozen exact budget and engine geometry

Each A/B/C arm receives exactly **340 unique full classical CryptoShield evaluations per development seed**.

For A and B:

- population size: 20
- shortlist size: 8
- parent count: 4
- proposals per parent: 4
- proposals per generation: 16
- generations: 20
- exact total: 20 + 20 x 16 = 340
- ITO non-inferiority tolerance: +0.02

Every unique candidate receiving a classical score is charged, including rejected proposals. Cached reads do not double-charge. ITO evaluations are counted separately.

## Frozen arms

### Arm A — multi-hotspot plateau repair

- shared fresh initial population;
- maximum-DDT-hotspot anchor;
- multi-hotspot Walsh plateau proposal geometry;
- exact 340 classical budget;
- frozen staged ITO-aware Pareto/NSGA-II shortlist and parent selection;
- no scalar weighted objective.

### Arm B — frozen Phase-1N single-worst-Walsh ablation

Identical to Arm A except proposal generation uses the frozen Phase-1N single-worst-Walsh operator. Same initial population, proposal count, exact budget, shortlist, parent count, ITO staging and terminal selection.

### Arm C — historical feasibility-first GA

Frozen historical comparator at exactly 340 classical evaluations. Descriptive only.

## Terminal reporting

For A and B report at minimum:

- exact classical evaluation count;
- ITO evaluation count;
- best terminal DU;
- terminal DU<=8 count;
- protected-classical terminal count (`NL>=100 AND max|LAT|<=64 AND degree>=6`);
- JOINT-target terminal count;
- hard-admissible count;
- structural-target count;
- minimum terminal ITO;
- terminal metrics and fingerprints;
- initial-population digest;
- proposal audit digest;
- multi-hotspot-guided and fallback proposal counts;
- deterministic scientific payload digest.

## Frozen development prerequisite for confirmation

All conditions are required across the five development seeds:

1. aggregate JOINT-target count in Arm A > Arm B;
2. Arm A reaches at least one JOINT-target candidate on at least 2/5 seeds;
3. DU bridge non-regression: seeds with terminal DU<=8 in A >= B and paired best-DU wins >= losses;
4. median terminal best DU(A) <= median terminal best DU(B);
5. aggregate protected-classical terminal count in A >= B;
6. median minimum terminal ITO(A) <= median minimum terminal ITO(B) + 0.02;
7. A/B/C each consume exactly 340 unique full classical evaluations on every seed, including rejected proposals;
8. A/B/C start from the same initial-population digest within each seed;
9. a fixed-seed rerun produces the same canonical scientific payload;
10. development seeds exactly match the registered Phase-1O set and confirmation seeds remain unused;
11. no neural model, neural fitness or Neural Oracle is executed.

If any condition fails, verdict is `phase1o_dev_fail`, confirmation remains blocked, no parameter is tuned in place, and the negative result is preserved.

If every condition passes, a separate confirmation protocol must be committed before any reserved confirmation seed is touched. Development parameters remain unchanged between development and confirmation.

## No-run lock

The scientific development matrix must not run until all of the following exist:

- issues #49–#53;
- this protocol;
- registered fresh seeds;
- red-first contract evidence;
- exact-budget implementation;
- green Python 3.10/3.11/3.12 CI;
- green historical benchmark;
- inspected PR diff;
- frozen scientific SHA;
- workflow preflight verifying frozen constants/seeds;
- explicit `PHASE1O_EXECUTE.md` authorization marker committed only after those engineering checks.

Ordinary unit/CI tests are allowed before authorization. Scientific seeds are not.

## Interpretation boundary

A development pass would support only the frozen mechanism comparison. It would not establish superiority to AES, deployment-grade security, physical side-channel resistance, or neural co-evolution. Gate 1 and the Neural Oracle remain separately governed.
