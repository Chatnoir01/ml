# Phase 2A panel reconstruction authorization

`AUTHORIZED_PHASE2A_PANEL_RECONSTRUCTION`

This marker authorizes only deterministic reconstruction and classical revalidation of the preregistered six-candidate Phase-2A panel from the frozen Phase-1O confirmation seeds.

It does **not** authorize any Phase-2A neural training and does not enable neural evolutionary pressure.

The reconstruction must replay the frozen Phase-1O Arm-A mechanism, match the frozen confirmation fingerprints seed-by-seed, run twice deterministically, revalidate the selected S-boxes classically, and emit the full permutations for commitment before any neural experiment.
