# Phase 2C-A — Artifact-only diagnostic execution marker

AUTHORIZED_PHASE2C_ARTIFACT_DIAGNOSTICS

## Frozen pre-marker source

`e5b1d7cf93768c1826721dd7e16cfdbe9f3f75ae`

Phase 2C-A is authorized only as deterministic analysis of the already-frozen Phase 2B artifacts from workflow run `34064310593` / scientific SHA `59066ad943fc85f24a21b4c2941cbcee4d23aeae`.

Verified before this marker:

- Phase 2C preregistration #103 exists;
- artifact-only execution lock #104 exists;
- Phase 0 CI is GREEN on Python 3.10, 3.11, and 3.12 at the pre-marker source;
- historical Phase 1 benchmark is GREEN at the pre-marker source;
- diff from merged Phase 2B is restricted to Phase 2C protocol, analyzer, CLI, tests, and locked workflow;
- analyzer has no neural scorer, Phase 2B validator, or Phase 2B arm-run import path;
- workflow installs no neural extras;
- input is pinned to the exact frozen Phase 2B workflow run and scientific SHA;
- exactly 27 arm artifacts are required;
- source artifact metadata/digests are frozen into a manifest;
- analysis is executed twice with reversed file order and must be byte-identical;
- no new neural training, evolution, Block-V scoring, or Phase 2B replay is authorized.

## Transparency

Issue #103 was created before detailed inspection of the frozen Phase 2B arm artifacts. After preregistration, an independent read-only local inspection of those already-existing artifacts was used to verify that the planned analyzer can run and indicated the preregistered `phase2c_artifacts_insufficient` category. This marker therefore authorizes a repository-controlled **reproduction** of an already-existing artifact analysis; it does not claim blind generation of new experimental data.

The repository workflow result is authoritative for the Phase 2C-A freeze. If it does not reproduce the frozen analyzer output deterministically, Phase 2C-A must not be frozen and must be investigated as a provenance/execution failure.

## Scope

Educational/defensive ToySPN research only. Full adaptive GA↔NN co-evolution remains prohibited.
