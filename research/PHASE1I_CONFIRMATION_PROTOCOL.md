# Phase 1I confirmation protocol — fresh-population Gate-1 test

## Status and timing

This confirmation protocol is committed **before any Phase-1I development result is available**. It therefore cannot be relaxed in response to the ten-neighborhood development batch.

The configuration entering confirmation is not chosen manually. It is defined as exactly the single configuration selected by the frozen Phase-1I development rule in `PHASE1I_DEV_PROTOCOL.md`. If no configuration meets the frozen development prerequisite, this confirmation protocol is not executed and all confirmation seeds remain unused.

## Scientific claim under test

The confirmatory question is:

> Can the automatically selected plateau-directed neighborhood reproduce hard-admissible 8×8 S-boxes from genuinely fresh random populations, under an exact matched full-evaluation budget, on previously untouched seeds?

A pass is intended to be the first evidence capable of changing global classical Gate 1 from RED to GREEN. It does not establish security of any deployed primitive and does not itself validate the later neural oracle.

## Frozen confirmation seeds

Use exactly these nine reserved seeds, once each:

`1801, 1811, 1823, 1831, 1847, 1861, 1871, 1873, 1877`

No development seed and no earlier Phase-1 seed may be substituted.

## Frozen arms and exact budget

For each seed:

### Selected directed arm

- start from a genuinely fresh random population;
- use the exact Phase-1I shared discovery configuration: 13 generations, 436 full classical evaluations;
- apply exactly the selected development neighborhood for 544 new unique full classical evaluations;
- total: exactly `980` full classical evaluations;
- no historical S-box, Phase-1B warm start, Phase-1H candidate, or hand-selected permutation may be injected.

### Matched comparator

- same fresh feasibility-first GA family;
- 30 generations;
- exactly `980` unique full classical evaluations;
- no directed repair.

The selected neighborhood parameters, proposal pool, cycle lengths, bridge caps, archive width, hotspot panel and cheap ranking rule are copied mechanically from the selected Phase-1I development configuration. No parameter may be retuned for confirmation.

## Frozen target definitions

Structural target:

- nonlinearity `>= 100`;
- differential uniformity `<= 8`;
- max linear correlation `<= 64`;
- algebraic degree `>= 6`.

Hard admissibility additionally requires:

- `|SAC - 0.5| <= 0.05`.

SAC remains excluded from the primary pairwise scientific ranking.

## Independent metric verification

Confirmation MUST use the separately implemented `independent_verify.py`, which does not import CryptoShield or the evolutionary evaluator.

For the best directed candidate and the best comparator candidate from every one of the nine seed pairs, the independent verifier must reproduce:

- nonlinearity exactly;
- differential uniformity exactly;
- max linear correlation exactly;
- algebraic degree exactly;
- SAC within absolute tolerance `1e-15`.

Any mismatch is an automatic confirmation failure, regardless of the search outcome.

Before confirmation execution, the independent verifier itself must pass the AES reference check:

- NL `112`;
- DU `4`;
- max correlation `32`;
- degree `7`;
- SAC `0.5048828125`.

## Frozen pairwise test

For each seed, compare the best directed and comparator candidates using the project’s existing primary security key, which excludes SAC as a secondary ranking signal.

Record directed win, comparator win, or tie.

On non-tied pairs compute the exact one-sided sign-test probability under `p=0.5`:

`P[X >= directed_wins]`.

## Frozen PASS criteria

Phase-1I fresh confirmation passes only if **all** of the following are true:

1. directed hard-admissible runs `>= 5/9`;
2. directed structural-target runs `>= 5/9`;
3. directed hard-admissible runs strictly exceed comparator hard-admissible runs;
4. directed structural-target runs strictly exceed comparator structural-target runs;
5. directed pairwise wins strictly exceed comparator wins;
6. exact one-sided sign-test `p < 0.05`;
7. median directed nonlinearity `>= 100`;
8. median directed differential uniformity `<= 8`;
9. median directed max linear correlation `<= 64`;
10. every directed and comparator arm consumes exactly `980` unique full classical evaluations;
11. seed/provenance checks confirm all nine confirmation seeds are reserved and previously unused by Phase-1I development;
12. independent verification matches the primary evaluator on all 18 best candidates as specified above.

There is no partial PASS and no post-hoc exception.

## Global Gate-1 rule

If all twelve criteria pass:

- Phase-1I fresh confirmation verdict = `PASS`;
- global classical Gate 1 becomes `GREEN` for the project’s toy/research S-box-generation claim;
- the neural-oracle research stage may be unblocked, while retaining classical hard gates as safeguards.

If any criterion fails:

- Phase-1I confirmation verdict = `FAIL`;
- global Gate 1 remains `RED`;
- neural-oracle work remains blocked;
- confirmation seeds are retired and may not be reused for tuning.

## Interpretation boundary

A PASS demonstrates reproducible search access to the project’s classical admissible region from fresh random populations under this experimental protocol. It does not prove optimality of the S-boxes, cryptographic security of a deployed cipher, or superiority over all published S-box construction methods.
