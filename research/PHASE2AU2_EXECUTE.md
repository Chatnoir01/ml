# Phase 2A-U2 Scientific Execution Authorization

AUTHORIZED_PHASE2AU2_FRESH_ORACLE_REQUALIFICATION

This marker freezes scientific execution only after the Phase 2A-U provenance defect was reproduced RED and repaired GREEN.

Pre-execution evidence for the immediately preceding code state:

- historical provenance defect reproduced by RED commit `b3e9238ff3ecdbb6d2ee344340bf30934617183d`;
- RED Phase 0 CI run `34060953692` failed as intended;
- complete Phase-2 neural seed registry committed;
- U2 seed registry frozen and disjoint from all known prior frozen/executed Phase-2 neural registries;
- U2 aggregation enforces pair count `8192` and exact split sizes `5734/1228/1230`;
- Phase 0 CI on PR #94 passed Python 3.10, 3.11 and 3.12;
- Phase 1 matched-budget benchmark on PR #94 passed;
- PR diff inspected and limited to Phase 2A-U/U2 provenance, protocol, runner, workflow and tests;
- Phase 2B remains locked by issue #87.

The scientific run is exactly **192 neural trainings** under the frozen two-block, 4-round Phase 2A-U2 protocol. No seed, threshold, candidate, architecture, input difference, endpoint, split, qualification rule, or budget may change based on observed results. No neural score may enter evolution in Phase 2A-U2.

This commit is the dedicated scientific execution SHA. Failure must be preserved; no in-place retuning is authorized.
