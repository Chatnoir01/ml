# Adversarial S-Box Research

A defensive, reproducible research framework studying classical evolutionary search over bijective 8×8 S-Boxes and whether a frozen neural distinguisher can provide bounded guidance in an educational cipher model. Neural scores never override the classical admissibility gates. The ToySPN is an experimental test vehicle, not a production cipher.

## Research status

The repository has progressed beyond its original Phase 0 initialization. The concise status and links to protocols, frozen findings, and provenance are maintained in the [research index](research/README.md).

Selected frozen results:

- **Phase 1O classical blind confirmation — PASS:** the frozen multi-hotspot search met the preregistered joint classical target on 6/9 confirmation seeds. This supports that specific matched-budget search mechanism only; it is not evidence of security or superiority to AES. See [the result](research/PHASE1O_CONFIRM_RESULT.md) and [Gate 1 limits](research/GATE1_STATUS.md).
- **Phase 2D bounded persistence — valid negative:** `phase2d_bounded_persistence_not_supported`; only two of seven support gates passed. See [the frozen result](research/PHASE2D_RESULT.md).
- **Phase 2F minimal-band neural pressure — valid negative:** `phase2f_minimal_band_pressure_not_supported`; all prerequisites passed, but the preregistered support gates were not jointly met. See [the frozen result and provenance](research/PHASE2F_RESULT.md), the [original protocol](research/PHASE2F_PROTOCOL.md), and [PR #117](https://github.com/Chatnoir01/ml/pull/117).

These findings answer different questions: Phase 1O evaluates a classical proposal/search mechanism; Phases 2D and 2F test specific forms of neural-score influence. A positive classical search result does not imply neural resistance, and the negative neural-guidance results are not failures of their workflow pipelines.

## Method and guardrails

The code provides dependency-free classical S-Box measurements, a permutation-preserving evolutionary search, deterministic datasets, and a small reversible ToySPN for controlled neural-distinguisher experiments. Phase-specific protocols record seeds, budgets, controls, decision thresholds, and provenance requirements.

- Classical security metrics are hard gates; a neural score cannot compensate for a weaker classical candidate.
- Held-out data is separated from evolutionary fitness and is scored only after terminal candidates are frozen.
- Frozen positive, negative, blocked, and inconclusive results are preserved; thresholds and seeds are not retuned after observing outcomes.
- Research and toy-model results do not establish production cryptographic security, AES resistance, physical side-channel resistance, or deployment readiness.

## Install and test

Requires Python 3.10 or newer:

```bash
python -m pip install -e '.[dev]'
pytest
```

Neural experiments require the optional `neural` dependency group. Individual preregistered phases may require a pinned runtime and execution authorization; consult that phase's protocol and workflow before running any scientific experiment. For example, Phase 2F locks NumPy to 2.5.3 and its scientific run is already complete; do not rerun or retune it as a substitute for its frozen result.

## Repository map

- `src/adversarial_sbox/` — classical metrics, evolutionary search, ToySPN, datasets, and phase implementations.
- `tests/` — unit and phase-contract tests.
- `scripts/` — experiment launchers and evidence validators.
- `research/` — preregistrations, execution records, reports, and provenance; start at [`research/README.md`](research/README.md).
- `results/` — committed experiment artifacts where applicable.

## Scope

This project is for defensive cryptographic research and reproducible experimentation. Its toy constructions and research findings are not encryption products, attack tooling, or evidence that any deployed cipher is vulnerable or secure.
