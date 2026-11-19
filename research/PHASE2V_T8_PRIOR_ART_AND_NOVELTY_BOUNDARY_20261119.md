# Phase 2V-T8: prior-art boundary (read-only literature note, 2026-11-19)

**This is NOT a novel general result about affine-equivalent S-Boxes.** Classical cryptography literature already establishes that S-Boxes with the same affine-equivalence invariants may have distinct multi-round behavior when placed into a fixed substitution-permutation network.

## Direct prior art
- **Anne Canteaut and Joëlle Roué (EUROCRYPT 2015)**, *On the Behaviors of Affine Equivalent Sboxes Regarding Differential and Linear Attacks*, LNCS 9056, pp. 45–74; DOI [10.1007/978-3-662-46800-5_3](https://doi.org/10.1007/978-3-662-46800-5_3), original [IACR-hosted paper](https://www.iacr.org/archive/eurocrypt2015/90560131/90560131.pdf). This work explicitly shows differences in multi-round expected differential/linear characteristics across affine-equivalent SBoxes despite shared equivalence invariants. Its studied SPN and theoretical endpoints differ from our **toy rotate-11 32-bit SPN and zero-byte count AUC**.
- **Anne Canteaut**, *Cryptographic Sboxes*, lecture notes, [Inria](https://www.paris.inria.fr/secret/Anne.Canteaut/poly.pdf). Standard formal background on vectorial Boolean functions, DDT/LAT, nonlinearity, affine equivalence.

## What the current T8 protocol can or cannot say
- Confirming *repeatable fixed-classical-score variation* across our 72 AES-affine variants is a source-bound, controlled **within-project empirical observation**, not proof of a new S-Box-invariant or new cryptanalytic method.
- T8 cannot conclude that our source-only one-round active-byte descriptor is a general **predictor** of security; a within-family correlation is descriptive. A genuinely new predictive result needs a preregistered, truly held-out **different base S-Box family**, no feature selection on T8 outcomes, and a classical baseline with matched budget.
- **No neural conclusion** follows: T8 has no fresh neural training. An independent neural-vs-classical hypothesis requires source/model-state provenance and the original Phase2U seal remains untouched.
- Our particular data sampling is *shared across candidates for paired comparison*, and the 12 groups are independent transformation/key/draw labels, **not 12 independent underlying AES S-Box families**. Effective scope is narrow.
- All primary and negative findings retained; no claim of worldwide novelty or resistance of deployed AES or real keys.

This note was added AFTER the 2026-11-19 T8 preregistration and first measurement and was not used to alter any outcome, key, candidate, parameter, acceptance threshold or script. Treat it as research-context disclosure, not a new T8 intervention.
