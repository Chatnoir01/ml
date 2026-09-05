# Phase 1O Blind Confirmation — Frozen Result

Status: `phase1o_confirm_pass`

Scientific execution SHA: `82db0eed2d69a85ea831c573406c0d58e86f5160`
Workflow run: `33984076226`
Aggregate artifact ID: `9974749795`
Aggregate artifact SHA-256: `8ea2b8f01a19095882aa56e9c335e6abefc0f2100225b6779d40e19381a2cf99`

## Preregistered confirmation set

Reserved seeds executed exactly once as the frozen confirmatory set:

`2609, 2617, 2621, 2633, 2647, 2657, 2663, 2671, 2683`

No Phase-1O development seed was reused. No search parameter, budget, threshold, ITO tolerance, or comparison arm was changed after the confirmation preregistration.

## Aggregate result

- Arm A JOINT-success seeds: **6/9**
- Arm A aggregate JOINT terminal candidates: **7**
- Arm B aggregate JOINT terminal candidates: **1**
- Seeds with terminal DU <= 8: A **6/9**, B **6/9**
- Paired best-DU wins/losses/ties for A: **1 / 1 / 7**
- Median terminal best DU: A **8**, B **8**
- Protected-classical terminal count: A **10**, B **2**
- Median minimum terminal ITO: A **6.84203431372549**, B **6.840563725490196**
- ITO non-inferiority tolerance: **+0.02**; PASS

The frozen JOINT target is:

- differential uniformity <= 8
- nonlinearity >= 100
- max |LAT| <= 64
- algebraic degree >= 6

Representative Arm-A successful candidates reached the JOINT target with DU=8, NL=100, max |LAT|=56, degree=7.

## Mandatory confirmation checks

All preregistered checks passed:

- `joint_aggregate_advantage = true`
- `joint_seed_successes_ge_5 = true`
- `du_bridge_nonregression = true`
- `median_best_du_nonregression = true`
- `classical_protection = true`
- `ito_noninferiority = true`
- `exact_classical_budgets = true`
- `same_initial_population = true`
- `deterministic_rerun = true`
- `reserved_seed_registry_exact = true`
- `neural_oracle_blocked = true`

Each A/B/C arm consumed exactly **340 unique full classical evaluations per seed**. All fixed-seed reruns reproduced the same canonical scientific payload. The Neural Oracle was not executed during Phase 1O confirmation.

## Interpretation boundary

This result is confirmatory evidence for the repository's frozen classical search mechanism under the preregistered matched-budget experiment. It is not evidence of superiority to AES or any deployed S-box, not proof of cryptographic security, not deployment readiness, not proof of physical side-channel resistance, and not evidence of neural resistance or successful GA↔NN co-evolution.

Per the preregistered Classical Gate-1 transition rule in issue #56, this confirmation PASS makes Classical Gate 1 GREEN and permits only Phase-2 neural engineering/experimental work under a new preregistered protocol. Classical hard constraints remain non-negotiable and may not be weakened in exchange for a neural score.
