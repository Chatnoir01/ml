# Phase 2A-R — Scientific Execution Authorization

AUTHORIZED_PHASE2AR_DIAGNOSTIC

Public preregistration: issue #60.

This marker authorizes only the frozen Phase-2A-R diagnostic decomposition. It does not qualify a Neural Oracle and cannot authorize GA↔NN feedback or Phase 2B.

Frozen base/result state:
- base main merge: `d32912b3818a15152edcceef38f5221446a9d01f`
- Phase 2A verdict: `phase2a_oracle_not_qualified`
- frozen classical panel digest: `35898535a0df0cfe64431e5f0b6142115d40e3dbeed4a973faa9ba70b1028a30`
- panel size: `6`

Fresh paired neural seeds:
- dataset seeds: `71001, 71009, 71023, 71039, 71059`
- model seeds: `81001, 81013, 81031, 81041, 81047`

Frozen blocked-permutation seeds:
- A: `91001`
- B: `91009`
- C: `91023`
- D: `91039`
- repetitions per regime: `10000`

Frozen bridge design:
- A: bit_relu_mlp, 4 rounds, differences 0x00000001 and 0x00000100
- B: byte_tanh_mlp, 4 rounds, differences 0x00000001 and 0x00000100
- C: byte_tanh_mlp, 5 rounds, differences 0x00000001 and 0x00000100
- D: byte_tanh_mlp, 5 rounds, differences 0x00010000 and 0x01000000

Exact budget:
- 8 cells
- 30 trainings per cell
- 60 trainings per regime
- **240 neural trainings total**

Frozen interpretation:
- A→B diagnoses the architecture/representation transition;
- B→C diagnoses the round-count transition;
- C→D diagnoses the input-difference-family transition;
- rank stability threshold remains Spearman rho >= 0.60;
- all four regimes must first satisfy the preregistered signal prerequisites;
- any diagnostic classification remains descriptive only.

No neural score may enter GA selection, mutation, ranking, acceptance, proposal generation, or any evolutionary pressure in Phase 2A-R. Phase 2B remains blocked regardless of this experiment's outcome.
