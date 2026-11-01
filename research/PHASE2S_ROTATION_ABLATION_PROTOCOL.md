# Phase 2S-C — Rotation-geometry ablation on frozen ToySPN (post-hoc)

**Status: exploratory mechanism diagnostic, not a blind confirmatory experiment.**
No new neural training, no cipher deployment and no change to the historical `ToySPN` implementation or frozen scientific results.

## Research motivation

A separate JavaScript exploratory probe of the six frozen, matched-classical-metric S-Boxes suggested that the distinguishing power of one ciphertext-XOR bit at 5 rounds varies sharply with the 32-bit internal rotation.

This is an observation from a *modified toy cipher*, NOT a statement that we proved the cause of the original `byte_tanh_mlp` peak, nor that an 11-bit rotation is secure.

## Intervention and controls

Hold constant:
- exact six Phase 2A-T S-Boxes (same fingerprints and DU=8/NL=100/max|LAT|=56/degree=7);
- original `ROUND_KEYS`, publicly known and fixed;
- identical positive/negative plaintext pairs across all S-Boxes and rotations;
- chosen differences `0x00000001` / `0x00000100`;
- depths 3, 4, 5, scoring method and splits.

Change ONLY one experimental cipher parameter:
- `rotation in {7,11,13}` bits, applied after all S-Box layers except the final round.

The implementation lives in a separate `RotatedToySPN` class and does not patch `src/adversarial_sbox/spn.py`. Critical regression: **rotation=11 produces byte-identical ciphertexts and one-bit holdout scores to original ToySPN** across every frozen S-Box and three depths.

Each of 108 cells (6 candidates × 3 depths × 2 differences × 3 rotations):
- 2,048 positive and negative *training* pairs per class;
- 4,096 positive and negative *held-out* evaluation pairs per class;
- exact matched plaintext sources supplied by Phase 2S-B and no train/test block reuse;
- one output XOR bit and its orientation selected using training only;
- signed holdout differential advantage (do not post-hoc take absolute);
- shuffled-label control on evaluation data;
- mean count of nonzero ciphertext-difference bytes in positive and negative held-out pairs (a crude, not exhaustive diffusion statistic).

These numbers are fixed for this **post-hoc** exploratory run. No multiple-testing-adjusted inferential claim or cross-cipher generalization is supported.

## Independent JavaScript preliminary observations (NOT official GitHub CI)

The local V8 exploratory calculation used xorshift32, 1,536/3,072 per-class train/evaluation pairs, and the original keys; it sampled six candidate S-Boxes for each rotation/depth/difference.

| Rotation | 3-round mean | 4-round mean | 5-round mean |
|---:|---:|---:|---:|
| 7 bits | 0.50066 | 0.43639 | 0.33776 |
| 11 bits (historical) | 0.49577 | 0.16499 | 0.02854 |
| 13 bits | 0.49895 | 0.15948 | 0.02382 |

Means pool the two differences and six candidates.

The 7-bit rotation preserved strong single-bit label differentiation at 5 rounds in this particular setup; 11/13 were much lower. This supports *testing a diffusion-geometry hypothesis*, but it is not evidence of real-world cipher weakness, uniquely optimal rotations, learned neural causality, or a universal cryptanalytic law.

The script and independent generation path used for Phase 2S-B have a different output distribution and random sampler from the Python rotation ablation. Do not claim numeric replication until the new Python source-run and independent output audit are available.

## Falsifiable follow-up

1. Verify original `ToySPN` encryption/decryption identity under rotation=11 before inspecting new ablation measurements.
2. Test whether the relative 5-round one-bit advantage for 7 vs 11/13 persists under independent Python samplers, using the exact declared grid.
3. Quantify whether a crude active-output-byte count distinguishes these cases. If it does not, do **not** treat all active bytes as evidence of adequate bit-level diffusion.
4. Compare bit-position movements across rounds/differences and alternative diffusion maps.
5. Only after the existing Phase 2R reproducibility gate and separate **prospective preregistration** would neural retraining under altered rotations provide direct evidence about the cause of the historical neural signal.
6. Benchmark and review any proposed new mechanism against stronger classical differential and linear attacks. Never equate weak one-bit distinguishability with full cipher security.

## Source/test/CI

- `src/adversarial_sbox/phase2s_rotation.py`
- `tests/test_phase2s_rotation.py`
- `.github/workflows/phase2s-retro.yml`

```bash
python -m pytest -q tests/test_phase2s_rotation.py
python -m adversarial_sbox.phase2s_rotation --smoke
python -m adversarial_sbox.phase2s_rotation > phase2s_rotation.json
```

**No new primitives, no AES claim, no real key recovery, no operational protection claim, no evidence of neural generalization.**
