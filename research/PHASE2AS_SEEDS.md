# Phase 2A-S — Frozen Neural Seeds

These seeds are frozen before any Phase 2A-S scientific training and implement issue #65.

Dataset seeds:
- 72001
- 72019
- 72031
- 72043
- 72053
- 72071
- 72089
- 72101

Model seeds:
- 82003
- 82013
- 82021
- 82037
- 82051
- 82067
- 82073
- 82087

Permutation seeds:
- R3: 92003
- R4: 92009
- R5: 92021

The eight dataset/model seed pairs are reused across all six frozen candidates, both frozen input differences, and depths 3/4/5. No seed may be replaced or retried because of its scientific result.

The exact training budget is 6 candidates × 2 differences × 8 paired replicates × 3 depths = **288 neural trainings**.

These values must be encoded in the Phase 2A-S implementation before the execution marker is created. The scientific workflow must reject any mismatch.