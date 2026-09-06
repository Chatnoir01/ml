# Phase 2A-T Scientific Execution Authorization

AUTHORIZED_PHASE2AT_DEPTH4_PEAK_REPLICATION

This marker authorizes exactly the preregistered fresh-seed Phase 2A-T experiment from issue #76 under execution lock #77.

Frozen design:
- panel digest: `35898535a0df0cfe64431e5f0b6142115d40e3dbeed4a973faa9ba70b1028a30`
- architecture: `byte_tanh_mlp`
- depths: 3, 4, 5
- differences: `0x00000001`, `0x00000100`
- paired replicates: 8
- exact trainings: 288
- blocked permutations: 10,000 per depth
- primary profile rule: H4>H3, H4>H5, R4>R3, R4>R5, M3>M4>M5; depth-4 p<0.05 required for full replication
- neural evolutionary pressure: forbidden

No scientific parameter may be changed after this commit based on observed results. Phase 2B GA↔NN remains blocked regardless of outcome.
