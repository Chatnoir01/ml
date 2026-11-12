# Research index

This index is a navigation aid for selected S-Box/ToySPN research tracks, not a claim that every repository experiment or workstream is scientifically or administratively closed. For the broader portfolio snapshot, see [the closure register dated 2 November 2026](RESEARCH_PORTFOLIO_CLOSURE_20261102.md) and its linked manifest. The registry explicitly records open blockers and administrative work.

## Selected frozen results

| Track | Status | Main finding | Protocol / result / provenance |
|---|---|---|---|
| Phase 1O classical S-Box search | Confirmatory result frozen: `phase1o_confirm_pass` | Arm A met the joint classical target on 6/9 reserved seeds (7 aggregate qualifying terminals vs 1 for Arm B). Median best DU was 8 for both arms; ITO non-inferiority passed. | [Protocol](PHASE1O_CONFIRM_PROTOCOL.md) · [Result](PHASE1O_CONFIRM_RESULT.md) · [Gate 1 status](GATE1_STATUS.md) |
| Phase 2D bounded neural-score persistence | Valid frozen negative: `phase2d_bounded_persistence_not_supported` | All prerequisites passed; only 2/7 support gates passed. The result does not support this preregistered one-generation persistence mechanism. | [Protocol](PHASE2D_PROTOCOL.md) · [Result](PHASE2D_RESULT.md) · [Machine aggregate](phase2d-result.json) · [Artifact manifest](phase2d-artifacts.json) |
| Phase 2E persistence diagnostics | Descriptive / forensic, not an efficacy result | Diagnostic analysis of the frozen Phase 2D artifact; it does not change or rescue the Phase 2D negative verdict. | [Protocol](PHASE2E_PROTOCOL.md) · [Report](PHASE2E_RESULT.md) · [Machine result](PHASE2E_RESULT.json) |
| Phase 2F minimal classical-band neural pressure | Valid frozen negative: `phase2f_minimal_band_pressure_not_supported` | All prerequisites passed; the seven preregistered gates were not jointly met. The actual run and provenance are summarized in the result record. | [Original protocol](PHASE2F_PROTOCOL.md) · [Result and provenance](PHASE2F_RESULT.md) · [Authorization marker](PHASE2F_EXECUTE.md) · [Merged PR #117](https://github.com/Chatnoir01/ml/pull/117) · [Workflow run 34316686692](https://github.com/Chatnoir01/ml/actions/runs/34316686692) |

## Interpreting statuses

- **PASS** means the specific frozen decision rule passed; it is not a general security claim.
- **Valid negative / not supported** means prerequisites and execution were valid, but the preregistered efficacy criteria were not met. Do not recast this as a CI or provenance failure.
- **Descriptive** means the analysis is not an efficacy test and cannot overturn its source experiment's verdict.
- **Blocked / inconclusive** must be distinguished from a valid scientific negative; consult the linked protocol and evidence register.

## Key implementation areas

- `src/adversarial_sbox/cryptoshield.py` — dependency-free classical S-Box metrics.
- `src/adversarial_sbox/evolution.py` — permutation-preserving classical evolutionary search and hard constraints.
- `src/adversarial_sbox/spn.py`, `datasets.py` — educational ToySPN and deterministic pair datasets.
- `src/adversarial_sbox/phase2f_*.py` — Phase 2F runner, fitness scoring, held-out validation, integrity gates, and aggregation.
- `.github/workflows/` — CI and phase-specific experiment pipelines.

For current repository-wide blockers and cross-project tracks beyond these selected experiments, consult the [portfolio closure register](RESEARCH_PORTFOLIO_CLOSURE_20261102.md). That dated register is an inventory baseline, not a declaration that all work is complete.
