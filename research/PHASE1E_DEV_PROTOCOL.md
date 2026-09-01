# Phase 1E — spectral/DDT-guided frontier continuation protocol

Status: **preregistered development only — not global Gate-1 evidence**.

## Question

Phase 1D showed that random swap/beam continuation preserves the historical
`DU=8` frontier but remains on the `NL=98` plateau. Phase 1E changes the operator
family rather than merely increasing the budget: proposals are guided by the
current worst Walsh component and/or the current worst DDT cell.

The narrow development question is:

> Starting from the exactly reproduced Phase-1B `NL=98 / DU=8 / corr=60`
> candidate, can a hotspot-guided permutation operator produce `NL>=100` while
> retaining `DU<=8`, max linear correlation `<=64`, and algebraic degree `>=6`?

This remains defensive/academic toy S-Box R&D. It is not an operational attack on
a deployed primitive.

## Historical start gate

Phase 1E imports the Phase-1D receipt function. Before development evidence is
accepted, it must reproduce exactly:

- seed `307` under the frozen Phase-1B configuration;
- `NL=98`;
- `DU=8`;
- maximum linear correlation `60`;
- algebraic degree `7`;
- fingerprint `d0260bcfbff19b1d43c1e2f41d923c6096d48ef0e3e4e1e78c088f81e02a1bcc`.

A mismatch invalidates the experiment.

## Seed isolation

Fresh Phase-1E development seeds, declared before results:

`907, 911, 919, 929, 937`

Reserved Phase-1E confirmation seeds, also declared before results:

`1009, 1013, 1019, 1021, 1031, 1033, 1039, 1049, 1051`

The reserved confirmation seeds cannot be consumed during development. They also
do not replace or reuse the unused Phase-1C/1D confirmation seeds; those remain
historically reserved and untouched.

## Guided operator

For the current frontier state, Phase 1E computes:

1. the non-zero output mask and input mask with largest absolute Walsh
   correlation, which is the component currently limiting vectorial NL;
2. the highest non-trivial DDT cell and the input positions contributing to it.

Candidate output swaps are sampled around those hotspot positions. Before a full
classical evaluation, each sampled pair receives an exact local proxy for:

- reduction in the selected Walsh hotspot magnitude; and
- reduction in the selected DDT hotspot count.

The selected pair is then evaluated with the unchanged full classical metric
pipeline. A new state can become the adaptive parent only if it remains inside the
structural frontier (`DU<=8`, max correlation `<=64`, degree `>=6`) and improves
the frozen continuation rank.

Guidance diagnostics are proposal-generation work, not additional candidate
fitness evaluations. The preregistered budget counts full classical S-Box
evaluations exactly. This experiment therefore compares algorithms at equal
fitness-evaluation budget, not equal CPU time.

## Equal-budget comparator

The comparator is the already-implemented Phase-1D adaptive frontier search:

- beam width `8`;
- random permutation-preserving swap mutation;
- same number of swaps as the guided configuration;
- same historical start;
- exactly the same number of full candidate evaluations.

This is intentionally stronger than comparing against direct non-adaptive random
mutations: Phase 1E must beat the prior adaptive operator family, not a weaker
control.

## Frozen budget

Every configuration uses, per development seed:

- `480` guided full candidate evaluations;
- `480` unguided adaptive full candidate evaluations.

No configuration receives extra fitness evaluations after observing results.

## Preregistered configurations

Declaration order is part of the tie-break rule.

1. `spectral32_s1`: spectral guidance, 32 pair proposals, 1 swap;
2. `spectral96_s1`: spectral guidance, 96 pair proposals, 1 swap;
3. `ddt64_s1`: DDT guidance, 64 pair proposals, 1 swap;
4. `hybrid64_s1`: hybrid guidance, 64 pair proposals, 1 swap;
5. `hybrid64_s2`: hybrid first swap plus one extra random swap, 64 pair proposals.

## Frozen selection rule

Configurations are ordered lexicographically by:

1. guided hard-admissible runs;
2. guided runs finishing with `NL>=100` and `DU<=8`;
3. the margin `(guided NL>=100/DU<=8 runs) - (unguided corresponding runs)`;
4. guided wins minus unguided wins under the frozen continuation rank;
5. higher median guided NL;
6. lower median guided DU;
7. lower median guided maximum linear correlation;
8. declaration order.

SAC cannot create a primary success. Hard admissibility still uses the unchanged
full constraints.

## Development stop rule

If **no guided configuration produces `NL>=100` with `DU<=8` on any development
seed**, Phase 1E confirmation is not executed and all nine Phase-1E confirmation
seeds remain unused.

If at least one configuration succeeds, exactly one configuration is selected by
the frozen rule. A separate confirmation protocol, including its acceptance
criteria, must then be committed **before** any reserved confirmation seed is used.

Regardless of the Phase-1E result, global Gate 1 does not pass from this warm-start
operator experiment alone. Fresh-population GA-vs-random evidence and repeated
hard admissibility remain separate requirements before the neural oracle phase can
start.
