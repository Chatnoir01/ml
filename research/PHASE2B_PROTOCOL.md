# Phase 2B — First controlled GA ← Neural Oracle pressure protocol

Public preregistration: issue #97  
Execution lock: issue #98  
RED-first implementation contract: issue #99  
Base `main`: `685bfdc47bd5ae8a45ecb8b4fca2d93030d847d8`

## Status

**PREREGISTERED / NOT EXECUTED**

Phase 2A-U2 is frozen as `phase2au2_oracle_qualified` and explicitly makes this separately preregistered matched-budget Phase 2B eligible. Full GA↔NN co-evolution remains out of scope.

## Scientific question

Under the frozen educational/defensive ToySPN setup, can the qualified 4-round neural Oracle be used as secondary evolutionary selection pressure to reduce held-out neural signal relative to the same classical search, without degrading protected classical metrics?

## Frozen classical fighter

Use the confirmed Phase-1O multi-hotspot Walsh search mechanism with unchanged geometry:

- population size: `20`
- shortlist size: `8`
- parent count: `4`
- proposals per parent: `4`
- proposals per generation: `16`
- generations: `20`
- exact classical budget: `340` unique full classical evaluations per arm/seed
- identical initial population digest across all arms for each seed

Hard classical constraints remain mandatory.

Protected classical key is exactly the existing:

`primary_security_key(metrics, HardConstraints())`

which is:

`(admissible, NL, -DU, -max|LAT|, algebraic_degree)`

A neural score may affect ordering **only when two or more selectable candidates have exactly equal protected classical keys**. It can never compensate for a worse protected key.

## Frozen fitness Oracle

Use exactly the qualified Phase 2A-U2 Block A scoring regime:

- architecture: `byte_tanh_mlp`
- ToySPN depth: `4`
- input differences: `0x00000001`, `0x00000100`
- pair count per training: `8192`
- exact split: train=`5734`, validation=`1228`, test=`1230`
- dataset seeds: `(176003, 176017, 176029, 176041, 176057, 176069, 176081, 176093)`
- model seeds: `(186007, 186019, 186031, 186043, 186061, 186073, 186091, 186103)`
- existing optimizer/training procedure unchanged

One candidate fitness-Oracle score is its mean neural advantage across exactly `16` trainings: 2 differences × 8 paired replicates.

**Lower neural advantage is better.**

No architecture, seed, pair count, split, depth, difference, optimizer/training procedure, or score definition may change after the scientific execution SHA is frozen.

## Frozen arms

### Arm C — classical control

Run the frozen Phase-1O search. At every eligible exact protected-key tie opportunity, compute the same real Oracle scores required by the matched ledger, but ignore those scores in selection. Classical ordering remains authoritative.

### Arm O — real Oracle pressure

At an eligible exact protected-key tie, lower frozen fitness-Oracle score is the first tie-breaker among candidates in that tie group. Outside exact protected-key equality, behavior is identical to Arm C.

### Arm S — shuffled-score negative control

At the same kind of exact protected-key tie, compute the same real Oracle scores, then deterministically permute score-to-candidate assignment within that tie group before applying the tie-break.

The shuffled RNG is derived deterministically as `evolution_seed + 10000`. No result-driven reseeding is allowed.

This arm tests whether any observed improvement is candidate-specific neural information rather than generic extra tie-breaking or noise.

## Frozen evolution seeds

Exactly nine fresh evolution seeds:

`(326011, 326023, 326033, 326047, 326051, 326063, 326071, 326087, 326099)`

Before execution, these seeds must be centrally registered and proven disjoint from all prior evolution seed registries in the repository.

No seed replacement or retry based on outcomes is allowed.

## Matched neural-scoring budget

Neural scoring is permitted only for exact protected-key tie groups that can change a selection decision.

Requirements:

1. no hidden candidate-wide neural prescoring;
2. every scored candidate is fingerprinted and receipted;
3. Arm C/O/S record exact eligible tie groups, candidate fingerprints, score counts and training counts;
4. every candidate score costs exactly 16 neural trainings;
5. within each seed, selection may use neural scores only up to a frozen matched opportunity cap shared by all three arms;
6. if raw eligible opportunity counts diverge across arms, the shared cap is the minimum realized eligible opportunity count among C/O/S for that seed;
7. extra opportunities beyond that cap are logged but cannot influence selection.

This preserves a matched information/compute budget without allowing result-driven candidate-wide scoring.

## Held-out terminal validation block V

Fitness Oracle seeds must never enter the primary endpoint.

After terminal candidates are frozen, evaluate each arm's terminal candidate on a fresh held-out Block V with exactly 16 trainings:

Dataset seeds:
`(276003, 276017, 276029, 276041, 276053, 276067, 276079, 276091)`

Model seeds:
`(286007, 286019, 286031, 286043, 286057, 286069, 286081, 286103)`

Block V uses the same:

- `byte_tanh_mlp`
- depth `4`
- differences `0x00000001`, `0x00000100`
- pair count `8192`
- split `5734 / 1228 / 1230`
- optimizer/training procedure

Before execution, all 16 Block-V seeds must be added to the complete Phase-2 neural seed registry and proven disjoint from every prior frozen/executed neural seed and from the fitness-Oracle seeds.

Block V is forbidden from all evolutionary selection code.

Primary endpoint per arm/seed: terminal candidate **held-out Block-V mean neural advantage**. Lower is better.

## Classical non-degradation gate

Phase 2B cannot PASS unless Arm O is non-degraded relative to Arm C on the paired terminal classical outcome.

Required:

- no worse JOINT-target status;
- no worse differential uniformity;
- no lower nonlinearity;
- no worse maximum absolute LAT correlation;
- no lower algebraic degree.

Any held-out neural improvement accompanied by protected-classical degradation fails the Phase-2B support criterion.

## Primary statistical criterion

Primary paired comparison: Arm O vs Arm C held-out Block-V terminal neural advantage across the nine frozen evolution seeds.

All required:

1. Arm O has lower held-out neural advantage than Arm C on at least `8/9` seeds;
2. one-sided exact paired sign-test `p < 0.05`;
3. mean paired reduction `(C - O) >= 0.02`;
4. the classical non-degradation gate passes;
5. Arm O beats Arm S on held-out neural advantage on at least `6/9` seeds;
6. mean held-out reduction of O versus C is strictly larger than the mean held-out reduction of S versus C.

If all six pass:

`phase2b_oracle_pressure_supported`

If provenance/budgets are valid but one or more support criteria fail:

`phase2b_oracle_pressure_not_supported`

If any provenance, seed, budget, Oracle-regime, execution-lock, held-out isolation, deterministic-receipt, or classical-protection prerequisite fails:

`phase2b_inconclusive_prerequisites`

## Determinism and receipts

Required before interpretation:

- exact 340-classical-evaluation ledger per arm/seed;
- same initial population digest across C/O/S per seed;
- exact neural training ledger for each candidate Oracle score;
- candidate fingerprint attached to each Oracle score;
- deterministic score payload SHA-256 receipts;
- deterministic shuffled-assignment receipts;
- exact fitness-vs-validation seed provenance;
- per-seed scientific payload deterministic on rerun;
- aggregate produced twice and byte-identical;
- scientific SHA frozen before any neural-pressure execution.

## Prohibited

- changing any threshold after observing Phase-2B results;
- changing the Oracle regime after observing results;
- changing evolution seeds or retrying a bad seed;
- using Block V in evolution;
- neural score compensating for a worse protected classical key;
- manual candidate selection;
- result-driven early stopping;
- hidden candidate-wide neural prescoring;
- retraining or adapting the Oracle from GA outcomes;
- full GA↔NN co-evolution.

## Execution gate

No scientific Phase-2B neural-pressure run may execute until every requirement in issue #98 is satisfied, including RED→GREEN contracts on Python 3.10/3.11/3.12, seed-registry hardening, historical Gate-1 and U2 regression checks, matched ledgers, held-out isolation, diff inspection, deterministic receipts, and a dedicated execution-marker commit freezing the scientific SHA.

## Scope boundary

Educational/defensive ToySPN research only.

This phase does not establish AES/deployed-cipher weakness, operational key recovery, physical side-channel resistance, production-security guarantees, or universal neural cryptanalysis.

Phase 2B is one-way **GA ← frozen Oracle** pressure only. Full adaptive GA↔NN co-evolution remains a later, separately gated phase.
