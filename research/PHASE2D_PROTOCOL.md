# Phase 2D — Bounded one-generation Oracle persistence

## Status

**PREREGISTERED / IMPLEMENTATION ONLY / SCIENTIFIC EXECUTION NOT AUTHORIZED**

Governing issues:

- #109 — preregistration
- #110 — execution lock

Phase 2D tests one new mechanism after the valid negative Phase 2B result and the valid Phase 2C-B forensic replay: a score-caused entrant may receive one persistence tag that is valid only for the corresponding selection stage of the next generation and only inside exact equality of the frozen protected classical key.

It is not adaptive bidirectional GA↔NN co-evolution.

## Frozen geometry

- population: 20
- shortlist: 8
- parents: 4
- proposals/parent: 4
- proposals/generation: 16
- generations: 20
- classical evaluations: exactly 340 per arm/seed
- protected key: `primary_security_key(metrics, HardConstraints())`
- no neural value or persistence tag may compensate for a worse protected key

## Arms

Exactly four matched arms are permitted:

- `C`: classical control; neural fitness scores are audit-only and cannot alter evolution.
- `O0`: fresh Phase-2B-style exact protected-key cutoff tie rule; no persistence.
- `OP1`: O0 plus one-generation protected persistence for candidates that enter selected membership because of the Oracle reorder.
- `SP1`: identical persistence machinery to OP1, but candidate↔score association is destroyed by one persistent shuffled-score RNG stream per seed.

No extra arm, persistence duration, weight, quota, decay rule or adaptive mechanism is allowed.

## Fresh evolution seeds

`(426011, 426023, 426037, 426049, 426061, 426073, 426089, 426101, 426113)`

They must be exact, unique and disjoint from the complete Phase-1 + Phase-2B evolutionary registry.

## Neural procedure

Frozen measurement procedure:

- architecture: `byte_tanh_mlp`
- ToySPN depth: 4
- input differences: `(0x00000001, 0x00000100)`
- pair count: 8192
- split: `(5734, 1228, 1230)`
- 8 paired dataset/model replicates per input difference
- 16 neural trainings per candidate score

### Fitness Block F

Dataset seeds:

`(376003, 376017, 376031, 376043, 376057, 376069, 376081, 376093)`

Model seeds:

`(386009, 386021, 386033, 386047, 386059, 386071, 386087, 386099)`

### Held-out Block W

Dataset seeds:

`(476003, 476017, 476029, 476043, 476057, 476071, 476083, 476099)`

Model seeds:

`(486007, 486019, 486031, 486043, 486061, 486073, 486091, 486103)`

F and W must be fresh against every prior Phase-2 neural seed and mutually disjoint. Block W is forbidden from evolutionary selection, implementation branching, score-budget decisions, threshold setting, retries or mechanism tuning.

## Exact neural budgets

Fitness exposure remains Phase-2B-sized:

- 32 candidate fitness scores per arm/seed
- no partial exact-key group scoring
- 512 fitness neural trainings per arm/seed
- 36 arm/seed cells
- exact fitness total: 18,432 neural trainings

After all 36 arm terminals are frozen, Block W is evaluated once:

- 36 terminal candidates
- 16 trainings per terminal
- exact Block-W total: 576 neural trainings

No additional exploratory scientific neural training is authorized.

## Persistence rule

Only `OP1` and `SP1` can create persistence tags.

When the arm's scored reorder changes selected membership at `shortlist` or `survival`, each fingerprint entering selected membership receives one tag for the same selection stage of generation `g+1`.

At that next stage:

1. protected classical key remains absolute;
2. inside one exact protected-key group, active tag precedes untagged candidate;
3. then arm score orders candidates (`OP1` real score, `SP1` shuffled association);
4. remaining equality preserves deterministic historical order.

A tag:

- cannot cross a strictly better protected key;
- exists for one next-generation corresponding stage only;
- expires after that stage whether used or not;
- does not stack;
- does not recursively extend itself merely by being active;
- can be created only by a real score-caused membership entry.

`O0` ignores tags entirely.

## Required instrumentation

Each selection stage must record generation, stage, cutoff, protected boundary key/group, selected membership before/after, score-caused entrants/exits, tag state before/after, tag use/non-use/expiry, score budget state and observational-only opportunities after closure.

Each generation must record shortlist, parents, proposals with direct parent, next population and ancestry needed for +1/+2/+5 persistence and terminal ancestry.

## Classical non-degradation

For support, OP1 terminal protected classical key must be no worse than both C and O0 for every one of the nine matched evolution seeds. Any worse seed fails support regardless of neural endpoint.

## Held-out support rule

`phase2d_bounded_persistence_supported` requires **all**:

1. OP1 higher +2 descendant-persistence rate than O0 on at least 6/9 seeds;
2. OP1 lower Block-W terminal neural advantage than O0 on at least 8/9 seeds;
3. one-sided exact paired sign test OP1 < O0 with `p < 0.05`;
4. `mean(O0 - OP1) >= 0.02` on Block W;
5. classical non-degradation on all 9 seeds;
6. OP1 lower Block-W terminal neural advantage than SP1 on at least 6/9 seeds;
7. mean OP1 Block-W neural advantage strictly lower than mean SP1.

If prerequisites are valid but any support gate fails:

`phase2d_bounded_persistence_not_supported`

If provenance, fresh seeds, exact budgets, matched populations, Block-W isolation, receipt integrity, terminal identity or CI/lock fails:

`phase2d_inconclusive_prerequisites`

No post-result threshold relaxation, seed replacement, protocol change or outcome-driven rerun is allowed.

## Execution marker

Scientific execution is prohibited until a later commit adds `research/PHASE2D_EXECUTE.md` containing exactly:

`AUTHORIZED_PHASE2D_BOUNDED_PERSISTENCE_EXPERIMENT`

Until then, all real 36-cell and Block-W workflows must remain dormant/fail closed.

## Scope

Educational/defensive ToySPN research only. No AES/deployed-cipher claim, operational key recovery, side-channel claim or adaptive attack deployment.
