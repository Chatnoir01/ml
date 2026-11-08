# Neural Crypto Lab V1 — original full exploratory seed 621017, observed 2026-11-08

**Observed experiment, not a security result. Do not retune the original seed or retrospectively redefine its success.**

## Authentic execution

- Original research branch proposal: PR #181, exact original source commit c36f87d863d5bd4ac8fea74f4815f0e0785a6a45.
- Actual GitHub Actions checked-out merge commit in receipt: 36e2bb3208f19ae359ec14160b67aeda78d7648b.
- GitHub Actions job: https://github.com/Chatnoir01/ml/actions/runs/42528775148 (SUCCESS).
- Original full-run ZIP artifact ID: 13636194059; SHA-256 of artifact ZIP: 9630d9cdb048a50972faad20cef701faa49a676788a87c5ef8dd345d051f5391.
- Individual canonical first/repeat JSON SHA-256: 2099f3380d2363db3460a101152a2c657fe7e2024629d186b8799d0cfd1fc164. Both runs were byte-identical.
- Protocol SHA-256 declared in result: 2ab9d951c78537c449724b60d550ba81eac5dece29858be7ecdfc5006fe1241c.
- Python 3.11.18, NumPy 2.4.6, CPU BLAS thread limits 1; complete frozen pip-freeze receipt stored in research/artifacts/neural_crypto_v1_seed_621017_dependencies.txt with SHA-256 79139c6ad9d9fba55821d542945fe801d7c33d1918b90b1292739cb866008e61.

## Observed results (1024 held-out message/key samples, 8 bits/message)

| Outcome | Value |
|---|---:|
| Bob held-out per-bit reconstruction accuracy, WITH key | 0.49755859375 |
| Fresh Eve #1 per-bit accuracy, WITHOUT key | 0.4908447265625 |
| Fresh Eve #2 per-bit accuracy, WITHOUT key | 0.5218505859375 |
| Validation Bob per-bit accuracy | 0.4984130859375 |
| Validation original training Eve per-bit accuracy | 0.5098876953125 |
| Identity plaintext control (attacker sees plaintext) | 1.0 |
| One-time XOR recovery control (Bob has fresh key) | 1.0 |

## Bounded interpretation

The **original frozen 200-step configuration failed to produce useful Bob reconstruction** on this full exploratory run: Bob was essentially at chance even when provided the shared key. Poor fresh Eve performance therefore cannot be interpreted as confidentiality. No secure learned cipher or cryptographic breakthrough resulted.

This run completed the fixed original protocol at one seed. Its checks passed, its outcome was unhelpful for communication, and it does NOT prove that neural encryption is impossible. No broad randomized multi-seed confirmatory test was performed, no chosen-plaintext attacker or actual deployable ciphertext was involved, and any future training-budget or architecture change must be a new preregistered experiment.

## Preservation

The original JSON output is preserved byte-for-byte in research/artifacts/neural_crypto_v1_seed_621017_result.json; installed dependency record is also archived there. GitHub Actions artifacts expire, so the repository copies serve long-term textual preservation. Keep the PR draft and research-only; no production integration or rewriting frozen prior outcomes.
