# Phase 2S-B — Matched single-bit ToySPN baseline (posthoc)

**Research only; post-hoc exploration; no new neural training, key recovery, or security assurance.**

## Why this experiment

The frozen Phase 2A-T result showed a peak in **between-S-Box neural score heterogeneity** at depth four (not in overall mean neural distinguishability). The six frozen candidates share DU=8, NL=100, max |LAT|=56 and degree=7, yet show different four-round neural scores.

An important simpler explanation is that their fixed-key ToySPN ciphertext XOR distributions leak differences detectable without any neural network. We therefore test an intentionally weak **one-bit differential distinguisher**, with a fully separated evaluation split, as a reference. This experiment is **not** a new blind confirmation: candidate panel, depths and prior results were visible before designing it.

## Frozen design and inputs

- Source: exact six-candidate Phase 2A-T panel, digest \`35898535a0df0cfe64431e5f0b6142115d40e3dbeed4a973faa9ba70b1028a30\`. This is a pinned historical digest, not a new measurement.
- Differences: \`0x00000001\` and \`0x00000100\`.
- Depths: 3, 4, 5 rounds of the existing 32-bit, four-byte ToySPN with fixed bit rotation 11.
- Key schedules: original public round keys; two deterministic perturbations (\`xor_perturbed\` and \`rotated_perturbed\`), defined by pure functions in \`phase2s_singlebit.py\`. These are **not secret key generations** or meaningful real-world key-security tests.
- Candidate, depth, difference and schedule grid: **6 × 3 × 2 × 3 = 108 cells**.
- Each cell: **2,048 positive and 2,048 negative training pairs**, then **4,096 positive and 4,096 negative separate evaluation pairs** (12,288 pairs/cell).
- Paired controls: plaintext-pair sources are generated independently of S-Box and schedule labels, then reused unchanged across those configurations for comparisons.
- All train and evaluation plaintext blocks are distinct; deterministic \`random.Random\` seeds are \`0x52010471\` (training) and \`0x520104A5\` (evaluation), with explicit overlap rejection. Python \`random.Random\` is **not a CSPRNG**, appropriate here only to a toy experiment.
- Label-shuffled diagnostic seed: \`0x520104E9\`, XORed with condition identifiers. This is a check for label association, not a calibrated hypothesis test.
- No extra evolution, training of \`byte_tanh_mlp\`, re-run of Phase 2A-T, or access to hidden model states.

## Exact one-bit baseline

From each pair, compute \`d = E_k(p0) XOR E_k(p1)\`.

- Positive class: \`p0 XOR p1 = delta\`.
- Negative class: two otherwise independent plaintext blocks; reject equal blocks and \`delta\` relations.
- On **training only**, measure \`g_b = Pr[d_b=1 | positive] - Pr[d_b=1 | negative]\` for each output bit \`b in 0..31\`.
- Select \`b* = argmax |g_b|\` with lowest-index tie breaking; freeze \`sign(g_b*)\` from training.
- On **evaluation only**, report **signed** \`A = sign(g_b*) * (Pr_test[d_b*=1 | positive] - Pr_test[d_b*=1 | negative])\`.
- For a binary score this is the signed \`2*(AUC-0.5)\` with orientation selected on training; negative evaluation scores are permitted and are **not** made positive after looking at evaluation results.
- Shuffle evaluation class labels deterministically for a corresponding negative control; output its signed score and compare descriptively.
- Summarize mean signed holdout score, between-candidate score range and absolute shuffled-label-control score by depth, difference and key schedule.
- For each of 18 condition groups (3 schedules × 3 depths × 2 differences), report **descriptive Pearson correlation across n=6 candidate scores with the frozen Phase 2A-T neural scores at the same depth**. This is post-hoc, not a pre-registered hypothesis test; if variance is zero return null instead of fabricating a correlation.
- Receipt includes SHA-256 of the canonical JSON measurements, not a proof of source integrity or a substitute for archived code SHA.

**A classical one-bit selector may detect signals absent from a coarse DU/NL scalar. This does not mean the neural model is redundant; it tests a deliberately limited rival hypothesis.**

## Evaluation safeguards

1. Run the 108-cell grid only on this separate Phase 2S branch. No change to earlier frozen scientific protocols.
2. Execute smoke tests in the Python 3.10–3.12 CI matrix before interpreting full-sample output.
3. Full 108-cell diagnostic is an **exploratory posthoc measurement**, not preregistered confirmatory evidence. Archive original JSON produced by code and its exact commit.
4. Require non-overlapping train/evaluation blocks, exact cell counts, deterministic outputs, no model state, no secret keys, no inferred deployed-cipher attacks.
5. Report both positive and negative findings, including cases where baseline does **not** match neural rank ordering or signal shape.
6. Do not select extra key schedules, differences, sample counts or metrics after results and call them a confirmation. New interpretations need separate frozen, genuinely new experiments.

## Distinguishing competing explanations

- **Strong baseline across schedules/depths:** an explanation relying entirely on special learned features or one fixed schedule becomes less plausible, but not disproven.
- **Baseline only with original keys:** a fixed-key interaction may matter. The neural models were not retrained under alternate keys, so this is not a direct key-generalization test.
- **Baseline fails while learned network still works:** the network may exploit multi-bit joint features, better representation, larger data or training; this still requires a separate controlled causal experiment.
- **Both baseline and network signals diminish at depth five:** this agrees with generic diffusion/near-chance effects, not proof of cryptographic security.

## Strict comparison and research novelty

Neural differential cryptanalysis and learned distinguishers are established prior art; see Aron Gohr, *Improving Attacks on Round-Reduced Speck32/64 Using Deep Learning* (CRYPTO 2019, https://eprint.iacr.org/2019/037).

A paper-quality new finding would require a **prospective**, independently tested mechanistic prediction on a new matched-metric panel, different key schedules and independent architectures, with classical baselines, registered outcomes, multiplicity control and external replication.

## Source and execution

- \`src/adversarial_sbox/phase2s_singlebit.py\` — deterministic generator, train-only bit selection, held-out evaluation and shuffled-label control.
- \`tests/test_phase2s_singlebit.py\` — geometry, integrity, trust and smoke regression tests.
- \`.github/workflows/phase2s-retro.yml\` — CI and optional archival artifact.

\`\`\`bash
python -m pytest -q tests/test_phase2s_singlebit.py
python -m adversarial_sbox.phase2s_singlebit --smoke
python -m adversarial_sbox.phase2s_singlebit > phase2s_singlebit.json
\`\`\`

**Do not label this result confirmed or CI-green until GitHub Actions completes its exact-head run.** No AES/deployed-cipher weakness, novel cryptographic primitive, proof of resistance, secure key exchange, or new physical side-channel result is claimed.
