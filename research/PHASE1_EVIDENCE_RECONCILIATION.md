# Phase 1 evidence reconciliation

Two concurrent Phase-1 research lines produced different-looking headline win
counts, but both correctly conclude that Gate 1 remains red.

## Historical frozen confirmation already on `main`

Source: `results/phase1/confirmation_b19938f.json`

- head: `b19938f81dd9d601eabdb5782af5054c31b9de5a`
- workflow: `33346116820`
- seeds: 12
- GA/random/tie by the historical full rank: **9 / 2 / 1**
- one-sided sign-test p: **0.03271484375**
- median constraint violation: **0.29 / 0.29**
- median NL: **96 / 96**
- median DU: **10 / 10**
- admissible candidates: **0 / 0**
- preregistered Gate 1: **red**

The significant sign test did not translate into structural median improvement.
Several paired wins were therefore driven by secondary rank coordinates.

## Concurrent stricter primary-comparison run

A separate branch later compared only the frozen primary security key
(admissibility, NL, DU, max-linear-correlation, degree):

- head: `d225a970592cc3c73c5b830af1622c59610ba53c`
- workflow: `33346715978`
- primary GA/random/tie: **5 / 2 / 2**
- one-sided sign-test p: **0.2265625**
- median NL: **98 / 96**
- median DU: **10 / 10**
- median max linear correlation: **60 / 64**
- admissible candidates: **0 / 0**
- verdict: **Gate 1 red**

### Independence correction

That stricter run was originally described on its branch as using fresh seeds.
After reconciling the concurrent history, seeds **211, 223, and 227** were found
to have already appeared in the earlier frozen confirmation. The stricter run is
therefore retained as useful historical/diagnostic evidence but **must not be
presented as fully blind confirmation**.

## Combined conclusion

The two experiments support the same conservative conclusion:

1. rank-level win counts can exaggerate progress when secondary metrics drive
   the ordering;
2. a stricter primary comparison shows a promising structural trend, especially
   NL and max-linear-correlation, but it is not statistically confirmed;
3. neither line produced a hard-admissible candidate;
4. Gate 1 remains red.

Phase 1B therefore uses a central seed registry, fresh development seeds, reserved
future confirmation seeds, a versioned `feasibility_first` search ranking, and a
separate primary-security comparison metric.
