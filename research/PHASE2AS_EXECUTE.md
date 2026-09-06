# Phase 2A-S Scientific Execution Authorization

AUTHORIZED_PHASE2AS_DEPTH_ATTENUATION

This marker authorizes exactly the preregistered Phase 2A-S experiment from issue #65 under execution lock #67.

Frozen design:
- panel digest: `35898535a0df0cfe64431e5f0b6142115d40e3dbeed4a973faa9ba70b1028a30`
- architecture: `byte_tanh_mlp`
- depths: 3, 4, 5
- differences: `0x00000001`, `0x00000100`
- paired replicates: 8
- exact trainings: 288
- deterministic blocked permutations per depth: 10,000
- primary attenuation thresholds: H5/H4 <= 0.50 and R5/R4 <= 0.75 with frozen monotonicity requirements
- neural evolutionary pressure: forbidden

No scientific parameter may be changed after this commit based on the observed result. Phase 2B GA↔NN remains blocked regardless of this experiment's outcome.
